# import packages
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
import sys
import os
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")
import processing_functions_March2025 as pf
from matplotlib.patches import Patch
sys.path.append('~/Santa_Cruz_WRM_Assistance/scripts')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Setup_SCWSM_Option_Analysis_CST import simSetup
print('import packages')

#%% define functions
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
def get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, columns):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates(filepath, combo, name_add)
    # current conditions
    df = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, combo[2], combo[1],
                                                                                    combo[3], combo[0], combo[4]),
        columns=columns)
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    df_filter = df_filter[df_filter['does_acct_get_assistance?'] > 0]
    #if len(df_filter) >= 100000:
    #    df_sample = df_filter.sample(n=100000, replace=False)
    #else:
    #    df_sample = df_filter.copy()  # If not enough rows, return all available data
    return df_filter


#%% import annual cost data ###
# set up parameters
filepath = '~/../../../scratch/users/jskerker/Santa_Cruz_WRM_Assistance/Figure6/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

# initialize dataframes
df_hist = pd.DataFrame()
df_modcool = pd.DataFrame()
df_cc = pd.DataFrame()

# current conditions
for combo in combinations:
    print(combo)
    name_add = 'Baseline_NoInf_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_hist = pd.concat([df_hist, df_annual], ignore_index=True)

# mod, cool
for combo in combinations:
    print(combo)
    name_add = 'Baseline_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_modcool = pd.concat([df_modcool, df_annual], ignore_index=True)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)
    name_add = 'Baseline_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_cc = pd.concat([df_cc, df_annual], ignore_index=True)

# add column for no assistance
df_hist.insert(0, 'tot_assist_none', 0)
df_modcool.insert(0, 'tot_assist_none', 0)
df_cc.insert(0, 'tot_assist_none', 0)

#%% look at distributions of ARs- get data
# import data
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))
columns = ['Date', 'does_acct_get_assistance?', 'AR', 'AR_assist_income', 'AR_assist_fixedDollar_$50',
           'AR_assist_fixedDollar_$100', 'AR_assist_fee', 'AR_assist_vol_55%', 'AR_assist_vol_80%']

df_hist_list = []
df_modcool_list = []
df_cc_list = []

for combo in combinations:
    print(combo)

    # current conditions data
    name_add = 'Baseline_NoInf_'
    df_filter = get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, columns)
    df_hist_list.append(df_filter)

    # modcool data
    name_add = 'Baseline_'
    df_filter = get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, columns)
    df_modcool_list.append(df_filter)

# climate change
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))
name_add = 'Baseline_'
# for combo in combinations:
#     print(combo)
#
#     # current conditions data
#     df_filter = get_assisted_bill_sample_with_max_dates(filepath, combo, name_add, columns)
#     df_cc_list.append(df_filter)
#
# # create dataframes from lists
# df_hist_hh = pd.concat(df_hist_list, ignore_index=True)
# df_modcool_hh = pd.concat(df_modcool_list, ignore_index=True)
# df_cc_hh = pd.concat(df_cc_list, ignore_index=True)

# save data
#df_hist_hh.to_csv(filepath + 'df_hist_hh_Fig6.csv')
#df_modcool_hh.to_csv(filepath + 'df_modcool_hh_Fig6.csv')
#df_cc_hh.to_csv(filepath + 'df_cc_hh_Fig6.csv')

# reimport data
df_hist_hh = pd.read_csv(filepath + 'df_hist_hh_Fig6.csv')
df_modcool_hh = pd.read_csv(filepath + 'df_modcool_hh_Fig6.csv')
df_cc_hh = pd.read_csv(filepath + 'df_cc_hh_Fig6.csv')

#%% Create boxplot
# create boxplots of annual costs for each type of assistance
fig = plt.figure(figsize=(15, 8))
gs = gridspec.GridSpec(2, 3, width_ratios=[1, 1, 1], height_ratios=[1, 1], wspace=0.25, hspace=0.45)
ft = 11
wd = 0.7
## subplots- assistance costs ##
ax00 = fig.add_subplot(gs[0, 0])
ax01 = fig.add_subplot(gs[0, 1])
ax02 = fig.add_subplot(gs[0, 2])
axes_all = [ax00, ax01, ax02]
df_hist_filter = df_hist.filter(like='tot_assist_', axis=1)
df_modcool_filter = df_modcool.filter(like='tot_assist_', axis=1)
df_cc_filter = df_cc.filter(like='tot_assist_', axis=1)
list_dfs = [df_hist_filter / 1e6, df_modcool_filter / 1e6, df_cc_filter / 1e6]
scenarios_list = ['Baseline', 'Moderate Climate \nwith Adaptation', 'Dry Climate \nwith Adaptation']
# labels_list = ['Income', 'Fixed: \n$25', 'Fixed: \n$50', 'Fixed: \n$100', 'Fee: \n100%', 'Vol.: \n50%', 'Vol.: \n70%', 'Vol.: \n90%']
labels_list = ['None', 'Income', 'Fixed: $50', 'Fixed: $100', 'Fee: 100%', 'Vol.: 55%', 'Vol.: 80%']
colors = ['dodgerblue', 'olivedrab', 'olivedrab', 'maroon', 'gold', 'gold']
# loop through subplots and climate scenarios
for i in range(3):
    box = axes_all[i].boxplot(list_dfs[i], showfliers=False, patch_artist=True, widths=wd)
    axes_all[i].set_xticklabels(labels_list, fontsize=ft, rotation=90)
    # axes_all[i].set_xticklabels(['', '', '', '', '', ''])
    axes_all[i].set_ylim(0, 18)
    axes_all[i].set_yticks(np.arange(0, 19, 3))
    axes_all[i].set_yticklabels(np.arange(0, 19, 3), fontsize=ft)
    axes_all[i].set_title(scenarios_list[i], fontsize=ft + 1, fontweight='bold')

    # Apply colors
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
    axes_all[i].grid(True, axis='y')

ax00.set_ylabel('Annual Assistance ($M)', fontsize=ft + 1, fontweight='bold')

# add custom legend
# Custom Legend with Patches
legend_patches = [
    mpatches.Patch(facecolor='dodgerblue', edgecolor='black', label='Income'),
    mpatches.Patch(facecolor='olivedrab', edgecolor='black', label='Fixed'),
    mpatches.Patch(facecolor='maroon', edgecolor='black', label='Fee'),
    mpatches.Patch(facecolor='gold', edgecolor='black', label='Volumetric')
]
# Add legend
leg = ax00.legend(handles=legend_patches, title='Assistance Type', loc="upper right", bbox_to_anchor=(1.01, 1.02),
                  frameon=True, fontsize=ft - 1)
leg.get_frame().set_edgecolor('white')

## AR distributions ##
cols = ['AR', 'AR_assist_income', 'AR_assist_fixedDollar_$50', 'AR_assist_fixedDollar_$100', 'AR_assist_fee',
        'AR_assist_vol_55%', 'AR_assist_vol_80%']
# subplots
ax10 = fig.add_subplot(gs[1, 0])
ax11 = fig.add_subplot(gs[1, 1])
ax12 = fig.add_subplot(gs[1, 2])
axes_all_AR = [ax10, ax11, ax12]
list_dfs = [df_hist_hh[cols], df_modcool_hh[cols], df_cc_hh[cols]]
# scenarios_list = ['Current conditions', 'Moderate, cool', 'Dry, hot']
# labels_list = ['Income', 'Fixed: \n$25', 'Fixed: \n$50', 'Fixed: \n$100', 'Fee: \n100%', 'Vol.: \n50%', 'Vol.: \n70%', 'Vol.: \n90%']
# colors = ['dodgerblue', 'olivedrab', 'olivedrab', 'olivedrab', 'salmon', 'gold', 'gold', 'gold']
# loop through subplots and climate scenarios
for i in range(3):
    axes_all_AR[i].plot([0.5, 6.5], [2.5, 2.5], color='k', linewidth=1.5, linestyle='--')
    box = axes_all_AR[i].boxplot(list_dfs[i], showfliers=False, patch_artist=True, widths=wd)
    axes_all_AR[i].set_xticklabels(labels_list, fontsize=ft, rotation=90)
    axes_all_AR[i].set_ylim(-0.5, 25)
    axes_all_AR[i].set_yticks(np.arange(0, 26, 5))
    axes_all_AR[i].set_yticklabels(np.arange(0, 26, 5), fontsize=ft)
    # axes_all_AR[i].set_title(scenarios_list[i], fontsize=10, fontweight='bold')
    axes_all_AR[i].set_xlim(0.5, 6.5)
    axes_all_AR[i].set_xlabel('Assistance Type', fontsize=ft + 1, fontweight='bold')

    # Apply colors
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
    axes_all_AR[i].grid(True, axis='y')  # , axis='y'

ax10.set_ylabel('AR (% of bill / income)', fontsize=ft + 1, fontweight='bold')

# add text labels
y1 = 22.7
y2 = 59.3
ax12.text(-14.38, y2, 'a', fontsize=18, fontweight='bold')
ax12.text(-6.88, y2, 'b', fontsize=18, fontweight='bold')
ax12.text(0.62, y2, 'c', fontsize=18, fontweight='bold')
ax12.text(-14.38, y1, 'd', fontsize=18, fontweight='bold')
ax12.text(-6.88, y1, 'e', fontsize=18, fontweight='bold')
ax12.text(0.62, y1, 'f', fontsize=18, fontweight='bold')

plt.savefig('../../outputs/Figures/Paper_Figure6_boxplots_AssistancePolicies_03Nov2025.jpg',
            bbox_inches='tight', dpi=300)
plt.show()