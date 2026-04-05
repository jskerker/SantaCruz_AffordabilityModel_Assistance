import numpy as np
import pandas as pd
from datetime import datetime

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


# function to calculate df of ARs from dfs of bills and mapped income
def get_ARs(df_bill, df_inc):
    # calculate affordability ratios
    bill_cols = [col for col in df_bill.columns if col.startswith('bill_')]

    AR_data = {}
    for col in bill_cols:
        # perform AR calcs
        AR_col_name = col.replace('bill', 'AR', 1)
        AR_data[AR_col_name] = (df_bill[col] / (df_inc['map_inc_1'] / 12)) * 100

    # create new dataframe
    df_AR = pd.DataFrame(AR_data)
    return df_AR


# function to get dataframes of bills, demand, and ARs
def get_data(real, dP, dT, dCV, demand, income_class, filepath, om):
    # import data
    filename = filepath + 'df_sample_' + income_class + '_P{}T{}_dCV{}_real{}_demand{}{}.csv'.format(dP, dT, dCV, real, demand, om)
    df = pd.read_csv(filename, index_col=0)

    prefixes = set(col.split('_')[0] for col in df.columns)

    # Create a dictionary to store separated DataFrames
    split_dfs = {}

    # Iterate over each prefix and date combination
    for prefix in prefixes:
        # print(prefix)
        # for date in dates:
        # Filter columns that match the current prefix and date
        # matching_cols = [col for col in df.columns if col.startswith(prefix) and date in col]
        matching_cols = [col for col in df.columns if col.startswith(prefix)]

        # Create a DataFrame with these columns if any columns match
        if matching_cols:
            # split_dfs[f"{prefix}_{date}"] = df[matching_cols]
            split_dfs[f"{prefix}"] = df[matching_cols]

    df_inc = split_dfs["map"]
    df_demand = split_dfs["demand"]
    df_bill = split_dfs["bill"]
    # calculate ARs
    df_AR = get_ARs(df_bill, df_inc)
    return df_demand, df_bill, df_AR

# function to get the cutoff start and end dates -- defined here manually
def get_dates(real, dP, dT, dCV, demand, filepath):
    # get dates to split at
    filename_tt = 'df_time_tracker_P{}T{}_dCV{}_real{}_demand{}.csv'.format(dP, dT, dCV, real, demand)
    df_time_tracker = pd.read_csv(filepath + filename_tt)
    print(df_time_tracker)
    # TODO: pick a cutoff date
    cutoff_date_start = datetime(2027, 10, 1)
    cutoff_date_end = datetime(2055, 10, 1)

    print('cutoff date start: ', cutoff_date_start)
    print('cutoff date end: ', cutoff_date_end)

    return cutoff_date_start, cutoff_date_end

# function to split a dataframe by the data
def split_df_by_date(df, cutoff_date_start, cutoff_date_end):
    no_inf_cols = []
    inf_cols = []
    disregard_cols = []

    # split columns of dataframe by date
    for col in df.columns:
        print(col)
        # Extract the month and year from the column name
        parts = col.split('_')
        if len(parts) == 3:
            month, year = int(parts[1]), int(parts[2])
            col_date = datetime(year, month, 1)

            # Categorize columns based on the cutoff date
            if col_date < cutoff_date_start:
                no_inf_cols.append(col)
                print('column with no inf: ', col_date)
            elif col_date < cutoff_date_end:
                inf_cols.append(col)
                print('col with inf: ', col_date)
            else:
                disregard_cols.append(col)
                print('col to disregard: ', col_date)

    # Create separate DataFrames for columns before and after the cutoff date
    df_no_inf = df[no_inf_cols]
    df_inf = df[inf_cols]
    return df_no_inf, df_inf


# import dataframe and get dataframe in long format with columns: account, demand (value), month, year
def get_long_df(df, var_name):
    df = df.reset_index()
    df_long = pd.melt(df, id_vars=['index'], var_name='Month_Year', value_name=var_name)
    # Rename the 'index' column to 'Account'
    df_long.rename(columns={'index': 'Account'}, inplace=True)

    # Extract Month and Year from the 'Month_Year' column
    df_long['Month'] = df_long['Month_Year'].str.extract(r'_(\d{1,2})_')[0]  # Extract the month
    df_long['Month'] = df_long['Month'].astype(int)
    df_long['Year'] = df_long['Month_Year'].str.extract(r'_(\d{4})$')[0]  # Extract the year
    df_long['Year'] = df_long['Year'].astype(int)

    return df_long

# load combinations of results into a long df
def load_combinations(combinations, income_class, om, filepath):
    # create empty dataframes
    df_long_all = pd.DataFrame()

    for combo in combinations:
        # get parameters from combination
        real = combo[0]
        dT = combo[1]
        dP = combo[2]
        dCV = combo[3]
        demand = combo[4]
        print(real, dT, dP, dCV, demand)

        # process data
        df_demand, df_bill, df_AR = get_data(real, dP, dT, dCV, demand, income_class, filepath, om)
        df_long = get_long_df(df_demand, 'Demand')
        df_long_bill = get_long_df(df_bill, 'Bill')
        df_long_AR = get_long_df(df_AR, 'AR')
        df_long['Bill'] = df_long_bill['Bill']
        df_long['AR'] = df_long_AR['AR']
        df_long['real'] = real
        df_long['dT'] = dT
        df_long['dP'] = dP
        df_long['dCV'] = dCV
        df_long['demand_scenario'] = demand
        df_long['income_class'] = income_class
        df_long['date'] = pd.to_datetime(df_long[['Year', 'Month']].assign(day=1))

        # concatenate data
        df_long_all = pd.concat([df_long_all, df_long], axis=0)

    return df_long_all


# function that takes in a monthly dataframe (make sure the index is the date column) and outputs
# an annually averaged df
def convert_monthly_to_annual_water_yr(df, col_name):
    # set index to date
    df = df.set_index('date')
    # add water year column to df
    df['water_year'] = df.index.year + (df.index.month >= 10)

    # get averaged annual data
    s_water_yr = df.groupby('water_year')[col_name].mean()
    df_water_yr = s_water_yr.to_frame()
    df_water_yr['date'] = pd.to_datetime(df_water_yr.index, format='%Y')  # add date column
    df_water_yr = df_water_yr.set_index('date')  # change date col to index
    return df_water_yr

# import result from df_results dataframe
def import_df_results(filepath, real, dT, dP, dCV, demand, name_add):
    df_results = pd.read_csv(filepath + 'df_results_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, dP, dT, dCV, real, demand))
    df_results['Date'] = pd.to_datetime(df_results['Date'])
    df_results['Month'] = df_results['Date'].dt.month
    df_results['Year'] = df_results['Date'].dt.year
    df_results = df_results.set_index('Date')
    return df_results

# get average water system results
def get_avg_precip(df_results):
    cols = ['unmetDemandMG', 'percReliability', 'precip_in', 'waterAvail', 'reservoirMG']
    df = pd.DataFrame(columns=cols)
    num_years = len(df_results) / 365  # np.round()
    unmetDemand = df_results['Urban_Water_Supply_Deficit_MGD'].sum() / num_years
    percRel = (df_results['Urban_Demand_Prior_Rationing'].sum() - df_results['Urban_Water_Supply_Deficit_MGD'].sum()) / \
              df_results['Urban_Demand_Prior_Rationing'].sum() * 100
    precipIn = np.sum(df_results['precip_LL_in']) / num_years
    waterAvail = np.sum(df_results['Flow_through_GHWTP_MGD']) / num_years
    reservoirMG = np.sum(df_results['LL_Reservoir_MG']) / num_years / 365.25
    df.loc[0] = {'unmetDemandMG': unmetDemand, 'percReliability': percRel, 'precip_in': precipIn,
                 'waterAvail': waterAvail, 'reservoirMG': reservoirMG}
    return df

# load results for one climate combination
def load_combinations_single(combo, income_class, om, filepath):
    # process data
    df_demand, df_bill, df_AR = get_data(combo[0], combo[2], combo[1], combo[3], combo[4], income_class, filepath, om)
    df_long = get_long_df(df_demand, 'Demand')
    df_long_bill = get_long_df(df_bill, 'Bill')
    df_long_AR = get_long_df(df_AR, 'AR')
    df_long['Bill'] = df_long_bill['Bill']
    df_long['AR'] = df_long_AR['AR']
    df_long['real'] = combo[0]
    df_long['dT'] = combo[1]
    df_long['dP'] = combo[2]
    df_long['dCV'] = combo[3]
    df_long['demand_scenario'] = combo[4]
    df_long['income_class'] = income_class
    df_long['date'] = pd.to_datetime(df_long[['Year', 'Month']].assign(day=1))

    return df_long

# function to process array of household data to long dataframe
def get_long_df_single(filepath, combo, name_add, om):
    arr_hh = np.load(filepath + 'arr_hh_data_{}P{}T{}_dCV{}_real{}_demand{}.npy'.format(name_add,combo[2], combo[1], combo[3], combo[0], combo[4]))

    # import household income data
    filepath_hh = '../../data/dcc_data/resampled_income_data.csv'
    df_hh = pd.read_csv(filepath_hh)

    # Create Monthly Dates (assuming starting from Jan 2020)
    start_date = "2020-10-01"
    num_months = arr_hh.shape[1]
    dates = pd.date_range(start=start_date, periods=num_months, freq="MS")
    # print(dates)

    # get accounts
    accounts = df_hh['account'].to_numpy()
    # get income
    income = df_hh['map_inc_1'].to_numpy()

    # Reshape into long format (flatten the first two dimensions)
    reshaped_data = arr_hh.reshape(-1, arr_hh.shape[2])

    # Create a DataFrame with account, date, and three parameter columns
    df_long = pd.DataFrame({
        "Account": np.repeat(df_hh["account"].values, num_months),
        "date": np.tile(dates, len(df_hh)),
        "Income": np.repeat(df_hh["map_inc_1"].values, num_months),
        "Demand": reshaped_data[:, 0],
        "Bill": reshaped_data[:, 1],
        "AR": reshaped_data[:, 2]
    })
    df_long['Year'] = df_long['date'].dt.year.astype("int16")
    df_long['Month'] = df_long['date'].dt.month.astype("int8")
    return df_long

# version of load_combinations_single where we filter for specific dates
def load_combinations_single_dates_filter(combo, om, filepath, name_add, df_dates):
    # process data
    df_long = get_long_df_single(filepath, combo, name_add, om)
    df_long = df_long.assign(
        real=combo[0], dT=combo[1], dP=combo[2], dCV=combo[3], demand_scenario=combo[4]
    )

    return df_long[df_long['date'].isin(df_dates)] # filter dates efficiently


# function to import objective values and decision variables for a seed
def get_opt_data(filepath, seed):
    # initialize lists
    decision_variables = []
    objective_values = []

    # open and process file
    filename = filepath + 'Borg_sim_test{}.set'.format(int(seed))
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:  # Skip comments and empty lines
                continue
            values = list(map(float, line.split()))  # Convert strings to floats
            decision_variables.append(values[:6])  # First 6 are decision variables
            objective_values.append(values[6:])  # Last 2 are objective values

    # Convert to numpy arrays for easier handling (optional)
    decision_variables = np.array(decision_variables)
    objective_values = np.array(objective_values)
    rof_thresholds, df_rank_order = separate_decision_vars(decision_variables)

    # process objective values data
    objective_values = objective_values * -1

    # Divide the second column (costs) by 1e7- 10s of millions of dollars
    objective_values[:, 1] /= 1000000  # 0

    # get dataframe with name of first value for each row
    df_inf_first = pd.DataFrame(
        {'FirstInf': df_rank_order.apply(lambda row: row.idxmin() if 1 in row.values else None, axis=1)})

    return objective_values, rof_thresholds, df_rank_order, df_inf_first


# function to separate decision variables into numpy array for rof thresholds and df for inf order
def separate_decision_vars(decision_variables):
    rof_thresholds = decision_variables[:, 0]
    rank_order = np.argsort(np.argsort(decision_variables[:, 1:])) + 1
    df_rank_order = pd.DataFrame(rank_order, columns=['transfer_soquel', 'transfer_sv', 'mcasr', 'desal', 'dpr'])

    # reorder columns
    new_order = ['desal', 'dpr', 'mcasr', 'transfer_soquel', 'transfer_sv']
    df_rank_order = df_rank_order[new_order]
    return rof_thresholds, df_rank_order


# define a function to import aggregate results for a single policy across SOWs
def aggregate_sows_for_policy(filepath, rof, inf_order, combinations, yr_start, yr_end):
    name_add = ''
    my_list = []
    for combo in combinations:
        # print(combo)
        # get time tracker data
        filename_tt = 'df_time_tracker_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3], combo[0],
                                                                                combo[4])
        df_time_tracker = pd.read_csv(filepath + filename_tt)
        if df_time_tracker.empty:
            inf_count = 0
            plan_date = 'nan'
            capex_cost = 0
            opex_cost_ann = 0
        else:
            inf_count = df_time_tracker.shape[0]
            plan_date = df_time_tracker['plan_date'].iloc[0]
            capex_cost = df_time_tracker['capex_cost'].sum()
            opex_cost_ann = df_time_tracker['opex_cost_annual'].sum()

        # get cashflow data
        filename_cashflow = 'df_cashflow_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3],
                                                                                  combo[0], combo[4])
        df_cashflow = pd.read_csv(filepath + filename_cashflow)
        df_cashflow['Date'] = pd.to_datetime(df_cashflow['Date'])
        df_cashflow['rev_mo_M'] = (df_cashflow['Opex_monthly_dollars'] + df_cashflow['IRF_revenue_needed']) / 1e6

        # filter data by years
        filtered_df = df_cashflow[(df_cashflow['Date'].dt.year >= yr_start) & (df_cashflow['Date'].dt.year < yr_end)]
        cashflow_rev = np.sum(filtered_df['rev_mo_M']) / (yr_end - yr_start)

        # import results data
        df_results = import_df_results(filepath, combo[0], combo[1], combo[2], combo[3], combo[4], name_add)
        # filter df_results
        filtered_df_results = df_results[(df_results.index.year >= yr_start) & (df_results.index.year < yr_end)]
        df_avg = get_avg_precip(filtered_df_results)
        # add row to list
        my_list.append({'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4],
                        'rof': rof, 'inf1': inf_order[0], 'inf2': inf_order[1], 'inf3': inf_order[2],
                        'inf4': inf_order[3], 'inf5': inf_order[4], 'inf_count': inf_count, 'plan_date': plan_date,
                        'capex_cost': capex_cost, 'opex_cost_ann': opex_cost_ann, 'cashflow_cost': cashflow_rev,
                        'unmetDemandMG': df_avg['unmetDemandMG'].iloc[0],
                        'percReliability': df_avg['percReliability'].iloc[0], 'precip_in': df_avg['precip_in'].iloc[0],
                        'waterAvail': df_avg['waterAvail'].iloc[0], 'reservoirMG': df_avg['reservoirMG'].iloc[0]})

    df = pd.DataFrame(my_list)
    return df


# define a function to import aggregate results for a single policy across SOWs
def aggregate_sows_for_hh_data(filepath, rof, inf_order, combinations):
    my_list_avg = []
    my_list_long = []
    for combo in combinations:
        print(combo)
        # load hh level data
        income_class = 'random'
        om = ''

        # get dates from cashflow data
        df_cashflow, max_rates, df_dates = get_max_rate_dates(filepath, combo)
        # df_cashflow, avg_rates, df_dates = get_max_rate_dates(filepath, combo)

        df_long = load_combinations_single_dates_filter(combo, income_class, om, filepath, df_dates)

        # get avg for each account
        df_group = df_long.groupby('Account')[['Demand', 'Bill', 'AR']].mean().reset_index()

        # new criteria for list entry
        entry = {'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4],
                 'rof': rof, 'inf1': inf_order[0], 'inf2': inf_order[1], 'inf3': inf_order[2], 'inf4': inf_order[3],
                 'inf5': inf_order[4], 'max_rate_T1': max_rates[0], 'max_rate_T2': max_rates[1],
                 'max_rate_T3': max_rates[2]}

        # repeat entry for length of df_group
        entries = [entry.copy() for _ in range(len(df_group))]

        # Add DataFrame columns to the list of dictionaries
        for idx, row in df_group.iterrows():
            entries[idx].update(row.to_dict())
        my_list_avg.extend(entries)

    return my_list_avg

# define a function to import aggregate results for a single policy across SOWs
def aggregate_sows_for_hh_data_medium(filepath, rof, inf_order, combinations):
    my_list_avg = []
    for combo in combinations:
        print(combo)
        # load hh level data
        income_class = 'random'
        om = ''

        # get dates from cashflow data
        df_cashflow, avg_rates, df_dates = get_medium_rate_dates(filepath, combo)
        # df_cashflow, avg_rates, df_dates = get_max_rate_dates(filepath, combo)

        df_long = load_combinations_single_dates_filter(combo, income_class, om, filepath, df_dates)

        # get avg for each account
        df_group = df_long.groupby('Account')[['Demand', 'Bill', 'AR']].mean().reset_index()

        # new criteria for list entry
        entry = {'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4],
                 'rof': rof, 'inf1': inf_order[0], 'inf2': inf_order[1], 'inf3': inf_order[2], 'inf4': inf_order[3],
                 'inf5': inf_order[4], 'avg_rate_T1': avg_rates[0], 'avg_rate_T2': avg_rates[1],
                 'avg_rate_T3': avg_rates[2]}

        # repeat entry for length of df_group
        entries = [entry.copy() for _ in range(len(df_group))]

        # Add DataFrame columns to the list of dictionaries
        for idx, row in df_group.iterrows():
            entries[idx].update(row.to_dict())
        my_list_avg.extend(entries)

    # df = pd.DataFrame(list)
    return my_list_avg  # , my_list_long

# define a function to import aggregate results for a single policy across SOWs- long-term average data
def aggregate_sows_avg_for_hh_data(filepath, rof, inf_order, combinations):
    my_list_avg = []
    for combo in combinations:
        print(combo)
        # load hh level data
        income_class = 'random'
        om = ''

        # get hh data in long df
        df_long = load_combinations_single(combo, income_class, om, filepath)

        # get avg for each account
        df_group = df_long.groupby('Account')[['Demand', 'Bill', 'AR']].mean().reset_index()

        # new criteria for list entry
        entry = {'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4],
                 'rof': rof, 'inf1': inf_order[0], 'inf2': inf_order[1], 'inf3': inf_order[2], 'inf4': inf_order[3],
                 'inf5': inf_order[4]}

        # repeat entry for length of df_group
        entries = [entry.copy() for _ in range(len(df_group))]

        # Add DataFrame columns to the list of dictionaries
        for idx, row in df_group.iterrows():
            entries[idx].update(row.to_dict())
        my_list_avg.extend(entries)

    return my_list_avg

# function that takes in a single climate SOW and returns: (1) cashflow df, (2) avg rates (tiers 1-3) above baseline, and (3) df of dates- dates where rate is above the min (or all dates if no dates > min)
def get_rate_dates(filepath, combo):
    # 1. import df_cashflow data
    filename_cashflow = 'df_cashflow_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3], combo[0],
                                                                              combo[4])
    df_cashflow = pd.read_csv(filepath + filename_cashflow)
    df_cashflow['Date'] = pd.to_datetime(df_cashflow['Date'])

    # 2. get "marginal" rates by adding up quant and IRF charges
    min_rates = []
    for tier in np.arange(1, 4):
        df_cashflow['Rate_T{}_upd'.format(tier)] = df_cashflow['Quant_T{}_upd'.format(tier)] + df_cashflow[
            'IRF_T{}_upd'.format(tier)]
        # 3. get max "marginal" rate
        min_value = df_cashflow['Rate_T{}_upd'.format(tier)].max()
        min_rates.append(min_value)

    # 4. extract dates with rates > min rate
    df_rate_dates = pd.to_datetime(df_cashflow.loc[df_cashflow['Rate_T1_upd'] > min_rates[0], 'Date'].tolist())

    # 5. get average rates where rates > min rate
    df_filtered = df_cashflow[df_cashflow['Rate_T1_upd'] > min_rates[0]]
    rates_avg = [df_filtered['Rate_T1_upd'].mean(), df_filtered['Rate_T2_upd'].mean(),
                 df_filtered['Rate_T3_upd'].mean()]
    return df_cashflow, rates_avg, df_rate_dates


# function that takes in a single climate SOW and returns: (1) cashflow df, (2) max rates (tiers 1-3), and (3) df of dates
def get_max_rate_dates(filepath, combo, name_add):
    # 1. import df_cashflow data
    filename_cashflow = 'df_cashflow_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1], combo[3], combo[0],
                                                                              combo[4])
    df_cashflow = pd.read_csv(filepath + filename_cashflow)
    df_cashflow['Date'] = pd.to_datetime(df_cashflow['Date'])

    # 2. get "marginal" rates by adding up quant and IRF charges
    max_rates = []
    for tier in np.arange(1, 4):
        df_cashflow['Rate_T{}_upd'.format(tier)] = df_cashflow['Quant_T{}_upd'.format(tier)] + df_cashflow[
            'IRF_T{}_upd'.format(tier)]
        # 3. get max "marginal" rate
        max_value = df_cashflow['Rate_T{}_upd'.format(tier)].max()
        max_rates.append(max_value)

    # 4. extract dates with max "marginal" rate
    df_max_rate_dates = pd.to_datetime(df_cashflow.loc[df_cashflow['Rate_T1_upd'] == max_rates[0], 'Date'].tolist())
    return df_cashflow, max_rates, df_max_rate_dates

# Income estimation sensitivity version
def get_max_rate_dates_IE(filepath, combo, name_add):
    # 1. import df_cashflow data
    filename_cashflow = 'df_cashflow_{}IE_P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1], combo[3], combo[0],
                                                                              combo[4])
    df_cashflow = pd.read_csv(filepath + filename_cashflow)
    df_cashflow['Date'] = pd.to_datetime(df_cashflow['Date'])

    # 2. get "marginal" rates by adding up quant and IRF charges
    max_rates = []
    for tier in np.arange(1, 4):
        df_cashflow['Rate_T{}_upd'.format(tier)] = df_cashflow['Quant_T{}_upd'.format(tier)] + df_cashflow[
            'IRF_T{}_upd'.format(tier)]
            
        
        # 3. get max "marginal" rate
        max_value = df_cashflow['Rate_T{}_upd'.format(tier)].max()
        max_rates.append(max_value)

    # 4. extract dates with max "marginal" rate
    df_max_rate_dates = pd.to_datetime(df_cashflow.loc[df_cashflow['Rate_T1_upd'] == max_rates[0], 'Date'].tolist())
    return df_cashflow, max_rates, df_max_rate_dates

# Income estimation sensitivity version
def get_max_rate_dates_IE2(filepath, combo, name_add, ie):
    # 1. import df_cashflow data
    filename_cashflow = 'df_cashflow_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, combo[2], combo[1], combo[3], combo[0],
                                                                              combo[4], ie)
    df_cashflow = pd.read_csv(filepath + filename_cashflow)
    df_cashflow['Date'] = pd.to_datetime(df_cashflow['Date'])

    # 2. get "marginal" rates by adding up quant and IRF charges
    max_rates = []
    for tier in np.arange(1, 4):
        df_cashflow['Rate_T{}_upd'.format(tier)] = df_cashflow['Quant_T{}_upd'.format(tier)] + df_cashflow[
            'IRF_T{}_upd'.format(tier)]

        # 3. get max "marginal" rate
        max_value = df_cashflow['Rate_T{}_upd'.format(tier)].max()
        max_rates.append(max_value)

    # 4. extract dates with max "marginal" rate
    df_max_rate_dates = pd.to_datetime(df_cashflow.loc[df_cashflow['Rate_T1_upd'] == max_rates[0], 'Date'].tolist())
    return df_cashflow, max_rates, df_max_rate_dates

# updated function (2/4/25) to aggregate monthly data for each SOW for a given policy
def aggregate_sows_for_policy_monthly(filepath, rof, inf_order, combinations, name_add):
    df_long = pd.DataFrame()
    cols = ['Urban_Demand_Prior_Rationing', 'Urban_Water_Supply_Deficit_MGD', 'precip_LL_in', 'Flow_through_GHWTP_MGD',
            'LL_Reservoir_MG', 'SLR_BigTrees']  # SLR_BigTrees

    for combo in combinations:
        print(combo)
        # get cashflow data
        filename_cashflow = 'df_cashflow_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1],
                                                                                    combo[3],
                                                                                    combo[0], combo[4])
        df_cashflow = pd.read_csv(filepath + filename_cashflow)
        df_cashflow['Date'] = pd.to_datetime(df_cashflow['Date'])
        df_cashflow['rev_mo_M'] = (df_cashflow['Opex_monthly_dollars'] + df_cashflow['IRF_revenue_needed']) / 1e6

        # keep Date, Opex_monthly_dollars, IRF_revenue_needed, and rev_mo_M columns
        df_filter = df_cashflow[['Date', 'Opex_monthly_dollars', 'IRF_revenue_needed', 'rev_mo_M']]
        df_filter.set_index('Date', inplace=True)

        # add uncertainties and policy information
        df_filter['real'] = combo[0]
        df_filter['dT'] = combo[1]
        df_filter['dP'] = combo[2]
        df_filter['dCV'] = combo[3]
        df_filter['demand'] = combo[4]
        df_filter['rof'] = rof
        df_filter['inf1'] = inf_order[0]
        df_filter['inf2'] = inf_order[1]
        df_filter['inf2'] = inf_order[2]
        df_filter['inf4'] = inf_order[3]
        df_filter['inf5'] = inf_order[4]

        # import results data
        df_results = import_df_results(filepath, combo[0], combo[1], combo[2], combo[3], combo[4], name_add)

        # get certain columns
        df = df_results[cols]

        # aggregate data to monthly
        df_monthly = df.resample('M').agg(
            {'Urban_Demand_Prior_Rationing': 'sum', 'Urban_Water_Supply_Deficit_MGD': 'sum', 'precip_LL_in': 'sum',
             'Flow_through_GHWTP_MGD': 'sum', 'LL_Reservoir_MG': 'mean', 'SLR_BigTrees': 'sum'})

        # change to first day of the month for index
        df_monthly.index = df_monthly.index.to_period('M').to_timestamp()

        # get metrics
        df_monthly = df_monthly.rename(columns={'Urban_Water_Supply_Deficit_MGD': 'UnmetDemand',
                                                'Flow_through_GHWTP_MGD': 'waterAvail'})  # unmet demand
        df_monthly['percReliability'] = (df_monthly['Urban_Demand_Prior_Rationing'] - df_monthly['UnmetDemand']) / \
                                        df_monthly['Urban_Demand_Prior_Rationing'] * 100  # reliability (%)

        # Merge on index
        df_merge = pd.merge(df_filter, df_monthly, left_index=True, right_index=True, how='inner')

        # add to df_long
        df_long = pd.concat([df_long, df_merge])

    return df_long

# function: updated to aggregate monthly hh data using array instead of df
def aggregate_sows_for_hh_data_long(filepath, rof, inf_order, combinations, name_add):
    df_list = []
    for combo in combinations:
        print(f"Processing: {combo}")
        # load hh level data
        #income_class = 'random' + name_add  # can change this to random_NoInf for no inf scenarios (I think)
        om = ''

        # get dates from cashflow data
        df_cashflow, max_rates, df_dates = get_max_rate_dates(filepath, combo, name_add)

        # get household data
        df_long = load_combinations_single_dates_filter(combo, om, filepath, name_add, df_dates)

        # add cols to hh data for: rof, first_inf, max_rate_T1
        df_long = df_long.assign(
            rof=rof,
            inf1=inf_order[0], inf2=inf_order[1], inf3=inf_order[2],
            inf4=inf_order[3], inf5=inf_order[4],
            max_rate_T1=max_rates[0]
        )

        # add to list
        df_list.append(df_long)

    return pd.concat(df_list, ignore_index=True)  # , df_cashflow, max_rates, df_dates

# function to compile 50th and 80th percentile AR information for figure 5
def compile_hh_data_ARquants(filepath, combinations, name_add):
    my_list = []

    for combo in combinations:
        print(combo)
        # 1. get the hh data
        income_class = 'random' + name_add  # can change this to random_NoInf for no inf scenarios (I think)
        om = ''
        # get dates from cashflow data
        df_cashflow, max_rates, df_dates = get_max_rate_dates(filepath, combo, name_add)
        # get household data
        df_long = load_combinations_single_dates_filter(combo, income_class, om, filepath, df_dates)

        # 2. get 50th and 80th percentiles for AR
        AR_50 = np.quantile(df_long['AR'], 0.5)
        AR_80 = np.quantile(df_long['AR'], 0.8)

        # 3. create df entry for new data
        my_list.append({'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4],
                        'AR_50': AR_50, 'AR_80': AR_80})

    df = pd.DataFrame(my_list)
    return df
