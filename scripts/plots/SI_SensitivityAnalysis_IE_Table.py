#%% import packages
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import itertools
import warnings
warnings.filterwarnings("ignore")
import sys
import processing_functions_March2025 as pf
print('import packages')

#%% define functions
def process_monthly_data_to_annual(df):
    # remove Water_Year 2021 data
    # df = df[df['Water_Year'] != 2021]

    # aggregate data to annual
    df_annual = df.groupby('Water_Year').agg({
        'tot_assist_income': 'sum',
        'tot_assist_fixedDollar_$50': 'sum',
        'tot_assist_fixedDollar_$100': 'sum',
        'tot_assist_fee': 'sum',
        'tot_assist_vol_55%': 'sum',
        'tot_assist_vol_80%': 'sum',
        'Date': 'count'  # Replace with the actual column you want to count
    })
    df_annual['count'] = df_annual['Date']
    return df_annual

# function to process monthly data to annual (like above) but with the added step of only including dates with the max rates
def process_monthly_data_to_annual_dates_filter(filepath, combo, name_add):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates(filepath, combo, name_add)
    # print(df_max_rate_dates)
    df = pd.read_csv(
        filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1],
                                                                                     combo[3], combo[0], combo[4]))
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    df['Water_Year'] = df['Date'].dt.year + (df['Date'].dt.month >= 10)
    df_annual = process_monthly_data_to_annual(df_filter)
    df_annual = df_annual[df_annual['count'] == 12]
    df_annual['real'] = combo[0]
    df_annual['dT'] = combo[1]
    df_annual['dP'] = combo[2]
    return df_annual


# function to process household assistance data with max date filtering
def get_hh_sample_with_max_dates(filepath, combo, name_add, columns):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates(filepath, combo, name_add)
    # current conditions
    df = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, combo[2], combo[1],
                                                                                    combo[3], combo[0], combo[4]),
        columns=columns)
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    # df_filter = df_filter[df_filter['does_acct_get_assistance?'] > 0]
    if len(df_filter) >= 100000:
        df_sample = df_filter.sample(n=100000, replace=False)
    else:
        df_sample = df_filter.copy()  # If not enough rows, return all available data
    return df_sample

# function to process household assistance data with max date filtering
def get_hh_sample_with_max_dates_IE(filepath, combo, name_add, ie, columns):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates_IE2(filepath, combo, name_add, ie)
    # current conditions
    df = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.parquet'.format(name_add, combo[2], combo[1],
                                                                                    combo[3], combo[0], combo[4], ie),
        columns=columns)
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    if len(df_filter) >= 100000:
        df_sample = df_filter.sample(n=100000, replace=False)
    else:
        df_sample = df_filter.copy()  # If not enough rows, return all available data
    return df_sample

# function to import the results for different income estimates
def import_df_results_IE(filepath, real, dT, dP, dCV, demand, name_add, ie):
    df_results = pd.read_csv(
        filepath + 'df_results_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, dP, dT, dCV, real, demand, ie))
    df_results['Date'] = pd.to_datetime(df_results['Date'])
    df_results['Month'] = df_results['Date'].dt.month
    df_results['Year'] = df_results['Date'].dt.year
    df_results = df_results.set_index('Date')
    return df_results


# updated function to aggregate monthly data for each SOW for a given policy
def aggregate_sows_for_policy_monthly_IE(filepath, rof, inf_order, combinations, name_add, ie):
    df_long = pd.DataFrame()
    cols = ['Urban_Demand_Prior_Rationing', 'Urban_Water_Supply_Deficit_MGD', 'precip_LL_in', 'Flow_through_GHWTP_MGD',
            'LL_Reservoir_MG']  # SLR_BigTrees

    for combo in combinations:
        print(combo)
        # get cashflow data
        filename_cashflow = 'df_cashflow_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, combo[2], combo[1],
                                                                                    combo[3],
                                                                                    combo[0], combo[4], ie)
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
        df_results = import_df_results_IE(filepath, combo[0], combo[1], combo[2], combo[3], combo[4], name_add, ie)

        # get certain columns
        df = df_results[cols]

        # aggregate data to monthly
        df_monthly = df.resample('M').agg(
            {'Urban_Demand_Prior_Rationing': 'sum', 'Urban_Water_Supply_Deficit_MGD': 'sum', 'precip_LL_in': 'sum',
             'Flow_through_GHWTP_MGD': 'sum', 'LL_Reservoir_MG': 'mean'})

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

#%% get monthly data- # of households, income- and vol-based assistance

# set up parameters
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations_mod = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
demand_All = ['Baseline']
combinations_cc = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

# all combinations
combinations = combinations_mod + combinations_cc
print(combinations)

# initialize dataframes
df_combined = pd.DataFrame()

# baseline conditions
filepath = '../../../../../../scratch/users/jskerker/Santa_Cruz_WRM_Assistance/Sims/'
list_scenario_data_baseline = []
for combo in combinations:
    print(combo)
    name_add = 'Baseline_'
    df = pd.read_csv(
        filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1],
                                                                                     combo[3], combo[0], combo[4]))
    df['real'] = combo[0]
    df['dT'] = combo[1]
    df['dP'] = combo[2]
    df['dCV'] = combo[3]
    df_combined = pd.concat([df_combined, df], ignore_index=True)

list_scenario_data_baseline = [df_combined]

# loop through IE scenarios
filepath = '../../../../../../scratch/users/jskerker/Santa_Cruz_WRM_Assistance/Sims_IE/'
name_add = 'Baseline_IE_'

income_estimates = np.arange(1, 11)
list_scenario_data = []
for ie in income_estimates:
    print('income estimate: {}'.format(ie))
    df_combined = pd.DataFrame()  # initialize df
    for combo in combinations:
        print(combo)
        df = pd.read_csv(
            filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, combo[2], combo[1],
                                                                                         combo[3], combo[0], combo[4], ie))
        df['real'] = combo[0]
        df['dT'] = combo[1]
        df['dP'] = combo[2]
        df['dCV'] = combo[3]
        df_combined = pd.concat([df_combined, df], ignore_index=True)
    list_scenario_data.append(df_combined)


#%% get count and assistance cost statistics data
cols = ['Count', 'tot_assist_income', 'tot_assist_vol_55%']

print('Baseline')
df = list_scenario_data_baseline[0]
for col in cols:
    print('50th and 80th {}: {} and {}'.format(col, np.nanquantile(df[col], 0.5),
                                           np.nanquantile(df[col], 0.8)))

for ie in income_estimates:
    for col in cols:
        print('\n Income Estimate: {}'.format(ie))
        df = list_scenario_data[ie-1]
        print('50th and 80th {}: {} and {}'.format(col, np.nanquantile(df[col], 0.5),
                                               np.nanquantile(df[col], 0.8)))
