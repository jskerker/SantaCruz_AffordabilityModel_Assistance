#%% import packages and define functions
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
import gc
warnings.filterwarnings("ignore")
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.append('../scripts')
#from Setup_SCWSM_Option_Analysis_CST import simSetup
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import processing_functions_March2025 as pf


# function to process cost data from monthly to annual scale
def process_monthly_data_to_annual(df):

    # aggregate data to annual
    df_annual = df.groupby('Water_Year').agg(
        tot_assist_income_sum=('tot_assist_income', 'sum'),
        count=('tot_assist_income', 'count')  # Count the number of entries in each group
    ).reset_index()
    return df_annual


# function to process monthly data to annual (like above) but with the added step of only including dates with the max rates
def process_monthly_data_to_annual_dates_filter(filepath, combo, name_add, ie):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates_IE2(filepath, combo, name_add, ie)
    df = pd.read_csv(
        filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, combo[2], combo[1],
                                                                                     combo[3], combo[0], combo[4], ie))
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    df_annual = process_monthly_data_to_annual(df_filter)
    df_annual = df_annual[df_annual['count'] == 12]
    return df_annual


# function to process household assistance data with max date filtering
def get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, ie, columns):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates_IE2(filepath, combo, name_add, ie)
    # current conditions
    df = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.parquet'.format(name_add, combo[2], combo[1],
                                                                                    combo[3], combo[0], combo[4], ie), columns=columns)
    df['Date'] = pd.to_datetime(df['Date'])

    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    return df_filter

print('import packages')

#%% import and process data- amount of assistance
## Question 3: How much will this cost? ##
# 3/29: added in filtering for dates with max rates
# import data
filepath = '../../../../../../scratch/users/jskerker/Santa_Cruz_WRM_Assistance/Sims_IE/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))
ie = 2
df_hist_cost = pd.DataFrame()
df_modcool_cost = pd.DataFrame()
df_cc_cost = pd.DataFrame()

for combo in combinations:
    print(combo)

    # current conditions data
    name_add = 'Baseline_IE_NoInf_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add, ie)
    df_hist_cost = pd.concat([df_hist_cost, df_annual], ignore_index=True)

    # modcool data
    name_add = 'Baseline_IE_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add, ie)
    df_modcool_cost = pd.concat([df_modcool_cost, df_annual], ignore_index=True)

# climate change
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)

    # dry, hot
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add, ie)
    df_cc_cost = pd.concat([df_cc_cost, df_annual], ignore_index=True)


#%% import and process household-level data
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))
columns = ['']
df_hist_list = []
df_modcool_list = []
df_cc_list = []
columns = ['Date', 'account', 'totalWaterCosts', 'AR', 'does_acct_get_assistance?', 'totalWaterCostsAssist_income',
           'AR_assist_income']

for combo in combinations:
    print(combo)
    # get household level data
    name_add = 'Baseline_IE_NoInf_'
    df_sample = get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, ie, columns)
    df_hist_list.append(df_sample)

    # modcool
    name_add = 'Baseline_IE_'
    df_sample = get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, ie, columns)
    df_modcool_list.append(df_sample)

# create dataframes from lists
df_hist = pd.concat(df_hist_list, ignore_index=True)
df_modcool = pd.concat(df_modcool_list, ignore_index=True)
del df_hist_list, df_modcool_list
# save as csv files
df_hist.to_csv(filepath + 'df_hist_Figure3_IE.csv', index=False)
df_modcool.to_csv(filepath + 'df_modcool_Figure3_IE.csv', index=False)
del df_hist, df_modcool
gc.collect()

# climate change
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)
    # get household level data
    name_add = 'Baseline_IE_'
    df_sample = get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, ie, columns)
    df_cc_list.append(df_sample)

# create df from list
df_cc = pd.concat(df_cc_list, ignore_index=True)
# save to csv
df_cc.to_csv(filepath + 'df_cc_Figure3_IE.csv', index=False)
del df_cc_list, df_cc

#%% import data once it's been created
df_hist = pd.read_csv(filepath + 'df_hist_Figure3_IE.csv')
df_modcool = pd.read_csv(filepath + 'df_modcool_Figure3_IE.csv')
df_cc = pd.read_csv(filepath + 'df_cc_Figure3_IE.csv')

#%% create boxplots of bills, AR, and assistance cost
fig = plt.figure(figsize=(12, 3.2))

gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1], wspace=0.32)
colors = ['paleturquoise', 'dodgerblue', 'paleturquoise', 'dodgerblue', 'paleturquoise', 'dodgerblue']
positions = [1, 1.6, 2.4, 3.0, 3.8, 4.4]
xtick_positions = [1.3, 2.7, 4.1]
xtick_labels=['Baseline  ', 'Moderate', 'Dry']
ft1 = 11
# subplot 1: water bills w/ and w/o assistance
ax00 = fig.add_subplot(gs[0, 0])
list_dfs = [df_hist['totalWaterCosts'], df_hist['totalWaterCostsAssist_income'], df_modcool['totalWaterCosts'], df_modcool['totalWaterCostsAssist_income'], df_cc['totalWaterCosts'], df_cc['totalWaterCostsAssist_income']]
box = ax00.boxplot(list_dfs, patch_artist=True, widths=0.45, showfliers=False, positions=positions)
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)
ax00.set_xlabel('Climate Scenario', fontsize=ft1)
ax00.set_xticks(xtick_positions)
ax00.set_xticklabels(xtick_labels, fontsize=ft1)
ax00.set_ylabel('Bills ($/month)', fontsize=ft1)
ax00.set_ylim(0, 400)
ax00.set_yticks(np.arange(0, 401, 50))
ax00.set_yticklabels(np.arange(0, 401, 50), fontsize=ft1)
ax00.set_title('Water Bills', fontsize=ft1+1, fontweight='bold')

# add custom legend
color_patches = [
    mpatches.Patch(color='paleturquoise', label='Before Assistance'),
    mpatches.Patch(color='dodgerblue', label='With Assistance')
]
legend = ax00.legend(handles=color_patches, loc='upper left', fontsize=ft1-1, frameon=False)
# Manually set the edge color of each legend patch
for patch in legend.get_patches():
    patch.set_edgecolor('black')  # Outline in black
    patch.set_linewidth(0.5)  # Set border width

x_limits = ax00.get_xlim()
print(x_limits)

# subplot 2: ARs w/ and w/o assistance
ax01 = fig.add_subplot(gs[0, 1])
list_dfs = [df_hist['AR'], df_hist['AR_assist_income'], df_modcool['AR'], df_modcool['AR_assist_income'], df_cc['AR'], df_cc['AR_assist_income']]
box = ax01.boxplot(list_dfs, patch_artist=True, widths=0.45, showfliers=False, positions=positions)
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)

ax01.set_xlabel('Climate Scenario', fontsize=ft1)
ax01.plot([0, 5], [2.5, 2.5], color='black', linewidth=1.5, linestyle='--')
ax01.set_xlim(0.5, 4.9)
ax01.set_xticks(xtick_positions)
ax01.set_xticklabels(xtick_labels, fontsize=ft1)
ax01.set_ylabel('AR (% of bill / income)', fontsize=ft1)
ax01.set_ylim(-0.2, 10)
ax01.set_yticks(np.arange(0, 11, 2))
ax01.set_yticklabels(np.arange(0, 11, 2), fontsize=ft1)
ax01.set_title('Affordability Burden', fontsize=ft1+1, fontweight='bold')

# subplot 3: annual costs of assistance
ax02 = fig.add_subplot(gs[0, 2])
list_dfs = [df_hist_cost['tot_assist_income_sum']/1e6, df_modcool_cost['tot_assist_income_sum']/1e6, df_cc_cost['tot_assist_income_sum']/1e6]
colors = ['dodgerblue', 'dodgerblue', 'dodgerblue']

# boxplot
box = ax02.boxplot(list_dfs, patch_artist=True, widths=0.4, showfliers=False)
# apply colors
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)

# add labels
ax02.set_xlabel('Climate Scenario', fontsize=ft1)
ax02.set_xticks(np.arange(1, 4))
ax02.set_xticklabels(xtick_labels, fontsize=ft1)
ax02.set_yticks(np.arange(0, 13, 2))
ax02.tick_params(axis='y', labelsize=11)
ax02.set_ylim(0, 12)
ax02.set_ylabel('Annual Assistance ($M)', fontsize=ft1)
ax02.set_title('Assistance Costs', fontsize=ft1+1, fontweight='bold')

plt.savefig('../../outputs/Figures/Figure3_IE.png', dpi=300, bbox_inches='tight')

#%% get statistics
# get data- water bills and ARs
print('current conditions')
print(df_hist[['totalWaterCosts', 'totalWaterCostsAssist_income']].median())
print(df_hist[['totalWaterCosts', 'totalWaterCostsAssist_income']].quantile(0.8))
print(df_hist[['AR', 'AR_assist_income']].median())
print(df_hist[['AR', 'AR_assist_income']].quantile(0.8))

print('dry, hot')
print(df_cc[['totalWaterCosts', 'totalWaterCostsAssist_income']].median())
print(df_cc[['totalWaterCosts', 'totalWaterCostsAssist_income']].quantile(0.8))
print(df_cc[['AR', 'AR_assist_income']].median())
print(df_cc[['AR', 'AR_assist_income']].quantile(0.8))

print('baseline  cost: {}, moderate climate cost: {}, dry climate  cost: {}'.format(df_hist_cost.median(), df_modcool_cost.median(), df_cc_cost.median()))

