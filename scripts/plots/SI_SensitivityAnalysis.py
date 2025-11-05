#%% Import packages
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
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")
import processing_functions_March2025 as pf
from matplotlib.patches import Patch
sys.path.append('/Users/jenniferskerker/Documents/GradSchool/Research/Equity/Model/Santa_Cruz_WRM_Assistance/scripts')
from Setup_SCWSM_Option_Analysis_CST import simSetup


def process_monthly_data_to_annual(df):
    # remove Water_Year 2021 data
    # df = df[df['Water_Year'] != 2021]

    # aggregate data to annual
    # df_annual = df.groupby('Water_Year', as_index=False)[['tot_assist_income', 'tot_assist_fixedDollar', 'tot_assist_fee', 'tot_assist_vol']].sum()
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
    return df_annual  # function to process monthly data to annual (like above) but with the added step of only including dates with the max rates


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
    # print(df_annual.head())
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


def import_df_results(filepath, real, dT, dP, dCV, demand, name_add):
    df_results = pd.read_csv(
        filepath + 'df_results_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, dP, dT, dCV, real, demand))
    df_results['Date'] = pd.to_datetime(df_results['Date'])
    df_results['Month'] = df_results['Date'].dt.month
    df_results['Year'] = df_results['Date'].dt.year
    df_results = df_results.set_index('Date')
    return df_results


# updated function (2/4/25) to aggregate monthly data for each SOW for a given policy
def aggregate_sows_for_policy_monthly(filepath, rof, inf_order, combinations, name_add):
    df_long = pd.DataFrame()
    cols = ['Urban_Demand_Prior_Rationing', 'Urban_Water_Supply_Deficit_MGD', 'precip_LL_in', 'Flow_through_GHWTP_MGD',
            'LL_Reservoir_MG']  # SLR_BigTrees

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

print('import packages & define functions')

#%% Get monthly data - # households, income- and vol-based assistance

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
filepath = '/Volumes/OneTouch/CAPs_Results/Results_Baseline_Oct2025/'
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

list_scenario_data = [df_combined]

# loop through SA scenarios
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
scenario_file_names = ['Demands_High_', 'Demands_Low_', 'DesalTime_Fast_', 'DesalTime_Slow_', 'InfCosts_High_',
                       'InfCosts_Low_', 'InterestRate_High_', 'InterestRate_Low_', 'CoS_High_', 'CoS_Low_']

scenario_names = ['Baseline', 'High Demands', 'Low Demands', 'Fast Desal. Deploy Time', 'Slow Desal. Deploy Time',
                  'High Infrastructure Costs', 'Low Infrastructure Costs', 'High Interest Rate',
                  'Low Infrastructure Rate', 'High Cost of Service',
                  'Low Cost of Service']  # 'Low Infrastructure Costs', , 'Low Interest Rate'

for scenario in scenario_file_names:
    print(scenario)
    df_combined = pd.DataFrame()  # initialize df
    for combo in combinations:
        print(combo)
        df = pd.read_csv(
            filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(scenario, combo[2], combo[1],
                                                                                         combo[3], combo[0], combo[4]))
        df['real'] = combo[0]
        df['dT'] = combo[1]
        df['dP'] = combo[2]
        df['dCV'] = combo[3]
        df_combined = pd.concat([df_combined, df], ignore_index=True)
    list_scenario_data.append(df_combined)

#%% get BASELINE household-level data
columns = ['Date', 'does_acct_get_assistance?', 'AR_assist_income', 'AR_assist_fixedDollar_$50', #'AR_assist_fixedDollar_$100', 'AR_assist_fee',
        'AR_assist_vol_55%'] #, 'AR_assist_vol_80%']

filepath = '/Volumes/OneTouch/CAPs_Results/Results_Baseline_Oct2025/'
name_add = 'Baseline_'
df_list = []
# loop through combinations
for combo in combinations:
    print(combo)

    # get AR data
    df_filter = get_hh_sample_with_max_dates(filepath, combo, name_add, columns)
    df_list.append(df_filter)

# convert list to df
df_hh = pd.concat(df_list, ignore_index=True)
# save df
filepath_save = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
df_hh.to_csv(filepath_save + 'df_hh_SA_{}.csv'.format(name_add))

#%% Compile household-level data
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
columns = ['Date', 'does_acct_get_assistance?', 'AR_assist_income', 'AR_assist_fixedDollar_$50',
           # 'AR_assist_fixedDollar_$100', 'AR_assist_fee',
           'AR_assist_vol_55%']  # , 'AR_assist_vol_80%']

# loop through scenarios
for scenario in scenario_file_names:
    print(scenario)
    df_list = []
    # loop through combinations
    for combo in combinations:
        print(combo)

        # get AR data
        df_filter = get_hh_sample_with_max_dates(filepath, combo, scenario, columns)
        df_list.append(df_filter)

    # convert list to df
    df_hh = pd.concat(df_list, ignore_index=True)
    # save df
    df_hh.to_csv(filepath + 'df_hh_SA_{}.csv'.format(scenario))

# Import household-level data
# import household data
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
scenario_file_names = ['Baseline_', 'Demands_High_', 'Demands_Low_', 'DesalTime_Fast_', 'DesalTime_Slow_',
                       'InfCosts_High_', 'InfCosts_Low_', 'InterestRate_High_', 'InterestRate_Low_', 'CoS_High_',
                       'CoS_Low_']

scenario_names = ['Baseline', 'High Demands', 'Low Demands', 'Fast Desal. Deploy Time', 'Slow Desal. Deploy Time',
                  'High Infrastructure Costs', 'Low Infrastructure Costs', 'High Interest Rate',
                  'Low Infrastructure Rate', 'High Cost of Service', 'Low Cost of Service']

list_scenario_hh_data = []

for scenario in scenario_file_names:
    print(scenario)
    df = pd.read_csv(filepath + 'df_hh_SA_{}.csv'.format(scenario))
    list_scenario_hh_data.append(df)


#%% Create CDFs for SI
# create cdfs of annual costs for each type of assistance
fig = plt.figure(figsize=(18, 8))
gs = gridspec.GridSpec(2, 4, width_ratios=[1, 1, 1, 1], height_ratios=[1, 1], wspace=0.2, hspace=0.25)

## subplots- cdfs ##
ax00 = fig.add_subplot(gs[0, 0])
ax01 = fig.add_subplot(gs[0, 1])
ax02 = fig.add_subplot(gs[0, 2])
ax03 = fig.add_subplot(gs[0, 3])
ax11 = fig.add_subplot(gs[1, 1])
ax12 = fig.add_subplot(gs[1, 2])
ax13 = fig.add_subplot(gs[1, 3])

colors = ['darkgrey',
          'royalblue', 'lightskyblue',  # demands
          'darkolivegreen', 'palegreen',  # desal
          'orangered', 'lightsalmon',  # inf costs
          'darkmagenta', 'lightpink',  # interest rates
          'gold', 'khaki']  # cost of service
linestyles = ['-', ':', '--', ':', '--', ':', '--', ':', '--', ':', '--']
linewidth = [1.8, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]

### first subplot: no. of HHs needing assistance ###
# loop through scenarios
i = 0
pos = ax00.get_position()
ax00.set_position([pos.x0 - 0.02, pos.y0, pos.width, pos.height])
for df, label in zip(list_scenario_data, scenario_names):
    data = df['Count'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax00.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax00.set_xlabel('No. of households each month', fontsize=11)
ax00.set_ylabel('CDF', fontsize=11)
ax00.set_title('Households Requiring Assistance', fontsize=11, fontweight='bold')
ax00.grid(True, alpha=0.3)
ax00.set_xlim([0, 11000])

### second subplot: income-based assistance ###
# loop through scenarios
i = 0
for df, label in zip(list_scenario_data, scenario_names):
    data = df['tot_assist_income'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax01.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax01.set_xlabel('Monthly assistance ($)', fontsize=11)
ax01.set_ylabel('CDF', fontsize=11)
ax01.set_title('Income-based Discount', fontsize=11, fontweight='bold')
ax01.grid(True, alpha=0.3)
ax01.set_xlim([0, 2e6])

### third subplot: volumetric assistance ###
# loop through scenarios
i = 0
for df, label in zip(list_scenario_data, scenario_names):
    data = df['tot_assist_fixedDollar_$50'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax02.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax02.set_xlabel('Monthly assistance ($)', fontsize=11)
ax02.set_ylabel('CDF', fontsize=11)
ax02.set_title('$50 Fixed Discount', fontsize=11, fontweight='bold')
ax02.grid(True, alpha=0.3)
ax02.set_xlim([0, 2e6])

### fourth subplot: volumetric assistance ###
# loop through scenarios
i = 0
for df, label in zip(list_scenario_data, scenario_names):
    data = df['tot_assist_vol_55%'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax03.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax03.set_xlabel('Monthly assistance ($)', fontsize=11)
ax03.set_ylabel('CDF', fontsize=11)
ax03.set_title('55% Volumetric Discount', fontsize=11, fontweight='bold')
ax03.grid(True, alpha=0.3)
ax03.set_xlim([0, 2e6])

### fifth subplot: income-based AR values ###
# loop through scenarios
i = 0
for df, label in zip(list_scenario_hh_data, scenario_names):
    data = df['AR_assist_income'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax11.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax11.set_xlabel('AR (% of bill / income)', fontsize=11)
ax11.set_ylabel('CDF', fontsize=11)
ax11.grid(True, alpha=0.3)
ax11.set_xlim([-1, 15])

### sixth subplot: fixed discount AR values ###
# loop through scenarios
i = 0
for df, label in zip(list_scenario_hh_data, scenario_names):
    data = df['AR_assist_fixedDollar_$50'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax12.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax12.set_xlabel('AR (% of bill / income)', fontsize=11)
ax12.set_ylabel('CDF', fontsize=11)
ax12.grid(True, alpha=0.3)
ax12.set_xlim([-1, 15])

### seventh subplot: volumetric AR values ###
# loop through scenarios
i = 0
for df, label in zip(list_scenario_hh_data, scenario_names):
    data = df['AR_assist_vol_55%'].dropna().sort_values()
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax13.plot(data, cdf, label=label, color=colors[i], linestyle=linestyles[i], linewidth=linewidth[i])
    i += 1

# add labels
ax13.set_xlabel('AR (% of bill / income)', fontsize=11)
ax13.set_ylabel('CDF', fontsize=11)
ax13.grid(True, alpha=0.3)
ax13.legend(loc='lower right', fontsize=10, bbox_to_anchor=(-2.85, 0.1))
ax13.set_xlim([-1, 15])

# add text
ax11.text(-5, 1.4, 'Monthly Assistance Costs', fontsize=12, fontweight='bold', rotation=90)
ax11.text(-5, 0.0, 'Monthly Affordability Ratios', fontsize=12, fontweight='bold', rotation=90)

plt.savefig('../../outputs/Figures/SI/SA_CDFs_10Oct2025.png', bbox_inches='tight')
plt.show()

