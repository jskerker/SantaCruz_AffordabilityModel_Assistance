#%% import packages & define functions
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import itertools
import time
import csv
import matplotlib.gridspec as gridspec
from statsmodels.distributions.empirical_distribution import ECDF
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
import os
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.append('/Users/jenniferskerker/Documents/GradSchool/Research/Equity/Model/Santa_Cruz_WRM_Assistance/scripts')
import processing_functions_March2025 as pf


# function to process cost data from monthly to annual scale
def process_monthly_data_to_annual_costs_HHs(df):
    # remove Water_Year 2021 data
    df = df[df['Water_Year'] != 2021]

    # aggregate data to annual
    # df_annual = df.groupby('Water_Year', as_index=False)[['tot_assist_income', 'tot_assist_fixedDollar', 'tot_assist_fee', 'tot_assist_vol']].sum()
    df_annual = df.groupby('Water_Year').agg({
        'tot_assist_income': 'sum',
        'Count': 'mean'
    }).reset_index()
    return df_annual


# function to process cost data from monthly to annual scale
def process_monthly_data_to_annual(df):
    # remove Water_Year 2021 data
    # df = df[df['Water_Year'] != 2021]

    # aggregate data to annual
    # df_annual = df.groupby('Water_Year')[['tot_assist_income']].sum()
    df_annual = df.groupby('Water_Year').agg(
        tot_assist_income_sum=('tot_assist_income', 'sum'),
        count_income=('tot_assist_income', 'count'),  # Count the number of entries in each group
        Count=('Count', 'mean')
    ).reset_index()
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
    df_annual = process_monthly_data_to_annual(df_filter)
    df_annual = df_annual[df_annual['count_income'] == 12]
    df_annual['real'] = combo[0]
    df_annual['dT'] = combo[1]
    df_annual['dP'] = combo[2]
    return df_annual


# function to process monthly data with filtering for the max rates
def process_monthly_with_dates_filter(filepath, combo, name_add):
    column_names = ['Date', 'tot_assist_income', 'Count']
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates(filepath, combo, name_add)
    # print(df_max_rate_dates)
    df = pd.read_csv(
        filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1],
                                                                                     combo[3], combo[0], combo[4]))
    df = df[column_names]
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]

    df_filter['real'] = combo[0]
    df_filter['dT'] = combo[1]
    df_filter['dP'] = combo[2]
    return df_filter


# get a statistic from a series
def get_statistic_from_series(series, stat):
    # dictionary of valid statistics
    valid_stats = ['mean', 'sum', 'max', 'min', 'std', 'median']
    # check if statistic is value
    if stat not in valid_stats:
        raise ValueError(f"Invalid statistic: {stat}. Choose from {valid_stats}")

    # Use getattr() to dynamically call the function and invoke it with ()
    return getattr(series, stat)()


# get statistic value and corresponding row
def get_closest_row_from_data(df_cost, col_name, stat_name):
    # get relevant statistic
    stat = get_statistic_from_series(df_cost[col_name], stat_name)
    # print('stat from function: {}'.format(stat))
    # find row where col value is closest to avg
    closest_row_idx = (df_cost[col_name] - stat).abs().idxmin()

    return df_cost.loc[closest_row_idx]  # retrieve full row


def get_assistance_by_month(combinations, filepath, name_add):
    columns = ['Date', 'account', 'totalWaterCosts', 'AR', 'does_acct_get_assistance?', 'totalWaterCostsAssist_income',
               'unafford_bill_difference', 'AR_assist_income']
    list_combinations = []

    # loop through combinations
    for combo in combinations:
        list_baseline = []
        print(combo)
        real = combo[0]
        dT = combo[1]
        dP = combo[2]
        dCV = combo[3]
        demand = combo[4]
        # get filtered dates
        df_filter = process_monthly_with_dates_filter(filepath, combo, name_add)
        # date_list = df_filter['Date'].tolist()
        # print(df_filter)

        # loop through dates
        for date in df_filter['Date'].iloc[0:20]:
            print(date)
            # get data from df_stat
            df_hh = pd.read_parquet(
                filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, dP, dT, dCV, real,
                                                                                            demand),
                columns=columns)  #
            df_hh_filter = df_hh[df_hh['Date'] == date]

            # get amount of assistance
            assistance = df_hh_filter['unafford_bill_difference'].sum()

            # get accounts getting assistance
            df_accts = df_hh_filter.loc[df_hh_filter['does_acct_get_assistance?'] == 1, 'account']
            list_baseline.append([assistance, df_accts])

        list_combinations.append(list_baseline)
    return list_combinations


# for a single simulation for getting the households (no inf):
# 1. loop through dates
# 2. for each date, get the households (list), the amount of assistance, and number of HHs
# 3. outputs: list of HHs to add to dictionary
# 4. outputs: new row (list of rows) with data
# 5. after finishing the loop- create dataframe of list of rows
def process_single_realization_NoInf(real, filepath):
    list_rows_by_date = []
    dict_dates = {}
    ## get households under scenario with no inf
    columns = ['Date', 'account', 'totalWaterCosts', 'AR', 'does_acct_get_assistance?', 'totalWaterCostsAssist_income',
               'unafford_bill_difference', 'AR_assist_income']
    name_add = 'Baseline_NoInf_'
    # get filtered dates
    df_filter = process_monthly_with_dates_filter(filepath, [real, 0, 100, 1.0, 'Baseline'], name_add)

    # get household data
    df_hh = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, 100, 0, 1.0, real,
                                                                                    'Baseline'), columns=columns)

    # loop through dates
    for date in df_filter['Date']:  # .iloc[0:20]
        print(date)
        # filter data based on date
        df_hh_filter = df_hh[df_hh['Date'] == date]

        # get amount of assistance
        assistance = df_hh_filter['unafford_bill_difference'].sum()

        # get accounts getting assistance
        list_accts = df_hh_filter.loc[df_hh_filter['does_acct_get_assistance?'] == 1, 'account'].tolist()
        dict_dates[date] = list_accts
        num_hhs = len(list_accts)

        # add row to list
        list_rows_by_date.append([real, 0, 100, 1.0, 'Baseline', date, assistance, num_hhs])

    df_monthly = pd.DataFrame(list_rows_by_date,
                              columns=['real', 'dT', 'dP', 'dCV', 'demand', 'date', 'assistance_cost',
                                       'num_households'])
    df_monthly = df_monthly.astype({
        'real': 'float',
        'dT': 'float',
        'dP': 'float',
        'dCV': 'float',
        'demand': 'string',
        'date': 'datetime64[ns]',
        'assistance_cost': 'float',
        'num_households': 'int'
    })
    return df_monthly, dict_dates


# for a single simulation with infrastructure investments:
# 1. loop through the temperature/precip states
# 2.    loop through the dates
# 3.        for each date, get total assistance, get total assistance from filtered and unfiltered hhs
# 4.        outputs: new row (list of rows) with data
# 5. create new dataframe with list of rows of data
def process_single_real_inf(real, filepath, dict_accts_by_date, dP_All, dT_All, dCV):
    list_rows_by_date = []
    dict_dates = {}
    ## get households under scenario with no inf
    columns = ['Date', 'account', 'totalWaterCosts', 'AR', 'does_acct_get_assistance?', 'totalWaterCostsAssist_income',
               'unafford_bill_difference', 'AR_assist_income']
    name_add = 'Baseline_'

    for dT in dT_All:
        for dP in dP_All:
            print('dT: {}, dP: {}'.format(dT, dP))
            # get household data
            df_hh = pd.read_parquet(
                filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, dP, dT, dCV, real,
                                                                                            'Baseline'),
                columns=columns)
            # get filtered dates
            df_filter = process_monthly_with_dates_filter(filepath, [real, dT, dP, dCV, 'Baseline'], name_add)

            # loop through dates
            for date in df_filter['Date']:  # .iloc[0:20]
                print(date)
                # filter data based on date
                df_hh_filter = df_hh[df_hh['Date'] == date]
                # get accounts requiring assistance in baseline realization & date
                baseline_accts = dict_accts_by_date[date]
                # print(baseline_accts)

                # get amount of assistance
                assistance_total = df_hh_filter['unafford_bill_difference'].sum()
                print('total monthly amt of assistance: ${}'.format(assistance_total))
                # get amount of assistance for accts requiring assistance in baseline
                df_hh_baseline = df_hh_filter[df_hh_filter['account'].isin(baseline_accts)]
                assistance_baseline_accts = df_hh_baseline['unafford_bill_difference'].sum()
                print('assistance in baseline accounts: ${}'.format(assistance_baseline_accts))

                # get amount of assistance for accts not originally needing assistance
                df_hh_not_baseline = df_hh_filter[~df_hh_filter['account'].isin(baseline_accts)]
                assistance_added_accts = df_hh_not_baseline['unafford_bill_difference'].sum()

                # number of accounts getting assistance
                accts = df_hh_filter.loc[df_hh_filter['does_acct_get_assistance?'] == 1, 'account']
                num_hhs = len(accts)
                # add row to list
                list_rows_by_date.append(
                    [real, dT, dP, dCV, 'Baseline', date, assistance_total, assistance_baseline_accts,
                     assistance_added_accts, num_hhs])

    # create dataframe from list
    df_monthly = pd.DataFrame(list_rows_by_date,
                              columns=['real', 'dT', 'dP', 'dCV', 'demand', 'date', 'assistance_cost_total',
                                       'assistance_cost_baseline_HHs', 'assistance_cost_new_HHs', 'num_households'])
    df_monthly = df_monthly.astype({
        'real': 'float',
        'dT': 'float',
        'dP': 'float',
        'dCV': 'float',
        'demand': 'string',
        'date': 'datetime64[ns]',
        'assistance_cost_total': 'float',
        'assistance_cost_baseline_HHs': 'float',
        'assistance_cost_new_HHs': 'float',
        'num_households': 'int'
    })
    return df_monthly

print('import packages & define functions')


#%% Import all monthly assistance data and filter by periods with max rate dates
filepath = '../../results/CAPs_Results/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations_baseline = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

df_hist_cost = pd.DataFrame()
df_modcool_cost = pd.DataFrame()
df_cc_cost = pd.DataFrame()

for combo in combinations_baseline:
    print(combo)

    # current conditions data
    name_add = 'Baseline_NoInf_'
    df_filter = process_monthly_with_dates_filter(filepath, combo, name_add)
    df_hist_cost = pd.concat([df_hist_cost, df_filter], ignore_index=True)

    # modcool data
    name_add = 'Baseline_'
    df_filter = process_monthly_with_dates_filter(filepath, combo, name_add)
    df_modcool_cost = pd.concat([df_modcool_cost, df_filter], ignore_index=True)

# climate change
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)

    # dry, hot
    df_filter = process_monthly_with_dates_filter(filepath, combo, name_add)
    df_cc_cost = pd.concat([df_cc_cost, df_filter], ignore_index=True)


#%% Loop through all realizations to get monthly assistance amounts
# loop through realizations
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
df_monthly_baseline_All = pd.DataFrame()
df_monthly_moderate_All = pd.DataFrame()
df_monthly_dry_All = pd.DataFrame()

for real in real_All:
    print('realization: {}'.format(real))
    # get list of accounts under baseline conditions
    df_monthly, dict_accts_lists = process_single_realization_NoInf(real, filepath)

    # moderate scenario: get assistance amounts under adaptation conditions
    df_monthly_moderate = process_single_real_inf(real, filepath, dict_accts_lists, [100], [0, 1], 1.0)

    # dry scenario: get assistance amounts under adaptation conditions
    df_monthly_dry = process_single_real_inf(real, filepath, dict_accts_lists, [80, 90], [4, 5], 1.2)

    # concatenate dataframes
    df_monthly_baseline_All = pd.concat([df_monthly_baseline_All, df_monthly], axis=0)
    df_monthly_moderate_All = pd.concat([df_monthly_moderate_All, df_monthly_moderate], axis=0)
    df_monthly_dry_All = pd.concat([df_monthly_dry_All, df_monthly_dry], axis=0)

# save dataframes as csv files
df_monthly_baseline_All.to_csv(filepath + 'df_monthly_baseline_Fig4.csv', index=False)
df_monthly_moderate_All.to_csv(filepath + 'df_monthly_moderate_Fig4.csv', index=False)
df_monthly_dry_All.to_csv(filepath + 'df_monthly_dry_Fig4.csv', index=False)


#%% Put together data for bar plots

# average
assistance = df_monthly_baseline_All['assistance_cost'].mean()
assistance_moderate = df_monthly_moderate_All[['assistance_cost_baseline_HHs', 'assistance_cost_new_HHs']].mean().tolist()
assistance_dry = df_monthly_dry_All[['assistance_cost_baseline_HHs', 'assistance_cost_new_HHs']].mean().tolist()
avg_combined = np.array([[assistance, 0, 0],
                         [assistance, assistance_moderate[0]-assistance, assistance_moderate[1]],
                         [assistance, assistance_dry[0]-assistance, assistance_dry[1]]])
print(avg_combined)

# max
assistance = df_monthly_baseline_All['assistance_cost'].max()
assistance_moderate = df_monthly_moderate_All[['assistance_cost_baseline_HHs', 'assistance_cost_new_HHs']].max().tolist()
assistance_dry = df_monthly_dry_All[['assistance_cost_baseline_HHs', 'assistance_cost_new_HHs']].max().tolist()
print('assistance cc: {}'.format(assistance_dry))
max_combined = np.array([[assistance, 0, 0],
                         [assistance, assistance_moderate[0]-assistance, assistance_moderate[1]],
                         [assistance, assistance_dry[0]-assistance, assistance_dry[1]]])
print(max_combined)

# min
assistance = df_monthly_baseline_All['assistance_cost'].min()
assistance_moderate = df_monthly_moderate_All[['assistance_cost_baseline_HHs', 'assistance_cost_new_HHs']].min().tolist()
assistance_dry = df_monthly_dry_All[['assistance_cost_baseline_HHs', 'assistance_cost_new_HHs']].min().tolist()
min_combined = np.array([[assistance, 0, 0],
                         [assistance, assistance_moderate[0]-assistance, assistance_moderate[1]],
                         [assistance, assistance_dry[0]-assistance, assistance_dry[1]]])
print(min_combined)


#%% Create bar plot
# set up parameters for bar plot
labels = ['Baseline', 'Assistance per \nhousehold', 'Number of \nhouseholds covered' , 'Interactions']
categories = ['Baseline  ', 'Moderate', 'Dry'] #, 'mod cool check', 'dry hot check']
colors = ['lightgray', 'salmon', 'gold', 'olivedrab', 'gold']
ft = 11
wd = 0.8

fig = plt.figure(figsize=(12, 3.2))
gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1], wspace=0.2)

# first subplot: avg
ax0 = fig.add_subplot(gs[0, 0])
bottom = np.zeros(len(categories))  # Initialize bottom at 0 for stacking
for i in range(avg_combined.shape[1]):
    ax0.bar(categories, avg_combined[:, i]/1e5, bottom = bottom, width=wd, color=colors[i], label=labels[i])
    bottom += avg_combined[:, i]/1e5
ax0.set_xlabel('Climate Scenario', fontsize=ft)
ax0.set_ylim(0, 14)
ax0.set_yticks(np.arange(0, 15, 2))
ax0.set_yticklabels(np.arange(0, 15, 2), fontsize=ft)
ax0.set_ylabel('Monthly Assistance\n(100K $)', fontsize=ft)
ax0.set_xticklabels(categories, fontsize=ft)
ax0.set_title('Average', fontsize=ft, fontweight='bold')

# second subplot: max
ax1 = fig.add_subplot(gs[0, 1])
bottom = np.zeros(len(categories))  # Initialize bottom at 0 for stacking
for i in range(max_combined.shape[1]):
    ax1.bar(categories, max_combined[:, i]/1e5, bottom = bottom, width=wd, color=colors[i], label=labels[i])
    bottom += max_combined[:, i]/1e5

ax1.set_xlabel('Climate Scenario', fontsize=ft)
ax1.set_ylim(0, 14)
ax1.set_yticklabels(np.arange(0, 15, 2), fontsize=ft)
ax1.set_xticklabels(categories, fontsize=ft)
ax1.set_title('Worst Case', fontsize=ft, fontweight='bold')

# third subplot: min
ax2 = fig.add_subplot(gs[0, 2])
bottom = np.zeros(len(categories))  # Initialize bottom at 0 for stacking
for i in range(min_combined.shape[1]):
    ax2.bar(categories, min_combined[:, i]/1e5, bottom = bottom, width=wd, color=colors[i], label=labels[i])
    bottom += min_combined[:, i]/1e5
#ax0.legend()
ax2.set_xlabel('Climate Scenario', fontsize=ft)
ax2.set_ylim(0, 14)
ax2.set_yticklabels(np.arange(0, 15, 2), fontsize=ft)
ax2.set_xticklabels(categories, fontsize=ft)
ax2.set_title('Best Case', fontsize=ft, fontweight='bold')

# add legend
ax2.legend(loc='upper left', title='Assistance Cost \nComponents', fontsize=ft-1.5, bbox_to_anchor=(0, 1.0), frameon=False, title_fontproperties={'size': ft-1.5, 'weight': 'bold'})
# add labels
ax2.text(-7.88, 14.4, 'a', fontsize=18, fontweight='bold')
ax2.text(-4.2, 14.4, 'b', fontsize=18, fontweight='bold')
ax2.text(-0.48, 14.4, 'c', fontsize=18, fontweight='bold')

plt.savefig('../../outputs/Figures/explanatory/Figure4.png', dpi=300, bbox_inches='tight')
plt.show()