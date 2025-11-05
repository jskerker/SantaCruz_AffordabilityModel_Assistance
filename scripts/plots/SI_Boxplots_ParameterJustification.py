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
        'tot_assist_fixedDollar_$35': 'sum',
        'tot_assist_fixedDollar_$40': 'sum',
        'tot_assist_fixedDollar_$45': 'sum',
        'tot_assist_fixedDollar_$50': 'sum',
        'tot_assist_fixedDollar_$55': 'sum',
        'tot_assist_fixedDollar_$60': 'sum',
        'tot_assist_fixedDollar_$65': 'sum',
        'tot_assist_fixedDollar_$70': 'sum',
        'tot_assist_fixedDollar_$75': 'sum',
        'tot_assist_fixedDollar_$80': 'sum',
        'tot_assist_fixedDollar_$85': 'sum',
        'tot_assist_fixedDollar_$90': 'sum',
        'tot_assist_fixedDollar_$95': 'sum',
        'tot_assist_fixedDollar_$100': 'sum',
        'tot_assist_fee': 'sum',
        'tot_assist_vol_40%': 'sum',
        'tot_assist_vol_45%': 'sum',
        'tot_assist_vol_50%': 'sum',
        'tot_assist_vol_55%': 'sum',
        'tot_assist_vol_60%': 'sum',
        'tot_assist_vol_65%': 'sum',
        'tot_assist_vol_70%': 'sum',
        'tot_assist_vol_75%': 'sum',
        'tot_assist_vol_80%': 'sum',
        'tot_assist_vol_85%': 'sum',
        'tot_assist_vol_90%': 'sum',
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
    if len(df_filter) >= 100000:
        df_sample = df_filter.sample(n=100000, replace=False)
    else:
        df_sample = df_filter.copy()  # If not enough rows, return all available data
    return df_sample
print('import packages & define functions')

#%% Import baseline data
# import baseline data
filepath = '/Volumes/OneTouch/CAPs_Results/Results_updated_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

df_hist = pd.DataFrame()

for combo in combinations:
    print(combo)

    # current conditions data
    name_add = 'Baseline_NoInf_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_hist = pd.concat([df_hist, df_annual], ignore_index=True)

#%% Import moderate and dry climate data
# import mod, cool and dry, hot data
filepath = '/Volumes/OneTouch/CAPs_Results/Results_updated_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

# initialize dataframes
df_modcool = pd.DataFrame()
df_cc = pd.DataFrame()

# mod, cool
for combo in combinations:
    print(combo)

    # current conditions data
    name_add = 'Baseline_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_modcool = pd.concat([df_modcool, df_annual], ignore_index=True)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

# mod, cool
for combo in combinations:
    print(combo)

    # current conditions data
    name_add = 'Baseline_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_cc = pd.concat([df_cc, df_annual], ignore_index=True)

#%% Get subset of dataframe columns
df_hist_subset = df_hist[['tot_assist_income', 'tot_assist_fixedDollar_$35', 'tot_assist_fixedDollar_$40', 'tot_assist_fixedDollar_$45', 'tot_assist_fixedDollar_$50', 'tot_assist_fixedDollar_$55', 'tot_assist_fixedDollar_$60','tot_assist_fixedDollar_$65', 'tot_assist_fixedDollar_$70', 'tot_assist_fixedDollar_$75', 'tot_assist_fixedDollar_$80', 'tot_assist_fixedDollar_$85', 'tot_assist_fixedDollar_$90','tot_assist_fixedDollar_$95', 'tot_assist_fixedDollar_$100', 'tot_assist_vol_40%', 'tot_assist_vol_45%', 'tot_assist_vol_50%','tot_assist_vol_55%', 'tot_assist_vol_60%', 'tot_assist_vol_65%',
                          'tot_assist_vol_70%', 'tot_assist_vol_75%', 'tot_assist_vol_80%', 'tot_assist_vol_85%', 'tot_assist_vol_90%']]
df_hist_subset = df_hist_subset / 1000000
cols = df_hist_subset.shape[1]

# extract statistics
med = df_hist_subset['tot_assist_income'].median()
avg = df_hist_subset['tot_assist_income'].mean()
perc25 = df_hist_subset['tot_assist_income'].quantile(0.25)
perc75 = df_hist_subset['tot_assist_income'].quantile(0.75)
perc10 = df_hist_subset['tot_assist_income'].quantile(0.1)
perc90 = df_hist_subset['tot_assist_income'].quantile(0.9)
std = df_hist_subset['tot_assist_income'].std()

#%% Create boxplots
# boxplots of annual assistance
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.grid(True, alpha=0.5)
bp = ax.boxplot(df_hist_subset, patch_artist=True)
plt.xticks(range(1, cols+1), ['Income', '$35', '$40', '$45', '$50', '$55', '$60', '$65', '$70', '$75', '$80', '$85', '$90', '$95', '$100', '40%', '45%', '50%', '55%', '60%', '65%', '70%', '75%', '80%', '85%', '90%'], rotation=90, fontsize=11)
ticks = plt.gca().get_xticklabels()

# Color each box
colors = ['gainsboro', 'white', 'white', 'white', 'lightskyblue', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'lightskyblue', 'white', 'white', 'white', 'lightskyblue', 'white', 'white', 'white', 'white', 'lightskyblue', 'white', 'white']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

# bold specific labels by index
bold_indices = [0, 4, 14, 18, 23]
for i in bold_indices:
    ticks[i].set_fontweight('bold')


# add lines separating assistance types
ax.plot([1.5, 1.5], [0, 4], color='k', linewidth=1.5, linestyle='--')
ax.plot([15.5, 15.5], [0, 4], color='k', linewidth=1.5, linestyle='--')
ax.text(5.5, 3.8, 'Fixed Dollar Amount', fontsize=12, fontweight='bold')
ax.text(18.25, 3.8, 'Volumetric Discount', fontsize=12, fontweight='bold')

# add labels
xmax = 27
plt.title('Boxplot of Annual Assistance Costs', fontsize=12)
plt.xlabel('Discount Quantity', fontsize=12)
plt.ylabel('Annual Cost ($M)', fontsize=12)
plt.ylim([0, 4])
plt.yticks(fontsize=10)
plt.xlim([0, xmax])

# Create custom legend
colors_legend = ['gainsboro', 'lightskyblue', 'khaki', 'white']
labels_legend = ['Income-based assistance', 'Chosen baseline discount quantities', 'Chosen future discount quantities', 'All other discounts tested']
legend_elements = [Patch(facecolor=colors_legend[i], edgecolor='black', linewidth=1, label=labels_legend[i]) for i in range(len(colors_legend))]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.savefig('../../outputs/Figures/SI/SI_Boxplots_AssistanceValues.jpg', bbox_inches='tight', dpi=300)
plt.show()