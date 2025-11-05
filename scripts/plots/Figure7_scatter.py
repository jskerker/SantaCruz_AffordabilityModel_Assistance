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
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D


# define processing function for aggregating simulations data
def compile_aggregated_sims_data(filepath, combinations, name_add, scenario_name, quantile):
    policy_names = ['No Assistance', 'Income', 'Fixed Dollar: $50', 'Fixed Dollar: $100', 'Fee', 'Volumetric: 55%',
                    'Volumetric: 80%']
    # create dfs
    df_combined = pd.DataFrame(
        columns=['real', 'dT', 'dP', 'dCV', 'scenario', 'policy', 'annual_avg_cost', 'AR_80perc'])
    # columns_list = ['AR', 'AR_assist_income', 'AR_assist_fixedDollar', 'AR_assist_fee', 'AR_assist_vol']

    for combo in combinations:
        print(combo)
        # get max rates
        df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates(filepath, combo, name_add)
        # assistance
        df = pd.read_parquet(
            filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, combo[2], combo[1],
                                                                                        combo[3], combo[0], combo[4]))
        df_filter = df[df['Date'].isin(df_max_rate_dates)]
        df_low = df_filter[df_filter['mapped_income'] < 87000]

        # get 80th percentile AR from simulation
        AR_80 = df_low[
            ['AR', 'AR_assist_income', 'AR_assist_fixedDollar_$50', 'AR_assist_fixedDollar_$100', 'AR_assist_fee',
             'AR_assist_vol_55%', 'AR_assist_vol_80%']].quantile(quantile)
        print(AR_80)
        print(type(AR_80))

        # get cost data
        df_cost = pd.read_csv(
            filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1],
                                                                                         combo[3], combo[0], combo[4]))
        df_cost['Date'] = pd.to_datetime(df_cost['Date'])
        df_cost_filter = df_cost[df_cost['Date'].isin(df_max_rate_dates)]
        years = len(df_max_rate_dates) / 12
        print('years: {}'.format(years))
        totalCosts = df_cost_filter[['tot_assist_income', 'tot_assist_fixedDollar_$50', 'tot_assist_fixedDollar_$100',
                                     'tot_assist_fee', 'tot_assist_vol_55%', 'tot_assist_vol_80%']].sum() / years
        new_value = pd.Series([0], index=['tot_no_assist'])
        totalCosts = pd.concat([new_value, totalCosts])
        print(totalCosts)
        print(type(totalCosts))

        # loop through policies to set up dataframe
        for i in range(len(totalCosts)):
            new_row = {'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4],
                       'scenario': scenario_name, 'policy': policy_names[i], 'annual_avg_cost': totalCosts[i],
                       'AR_80perc': AR_80[i]}
            df_combined = pd.concat([df_combined, pd.DataFrame([new_row])])

    return df_combined

print('import packages & define functions')

#%% Compile data for 3 climate scenarios
# 1. current conditions
filepath = '/Volumes/OneTouch/CAPs_Results/Results_Baseline_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

df_combined_hist = compile_aggregated_sims_data(filepath, combinations, name_add='Baseline_NoInf_', scenario_name='Baseline', quantile=0.8)
df_combined_hist.to_csv(filepath + 'df_combined_hist_Fig7.csv')

# 2. moderate scenario
filepath = '/Volumes/OneTouch/CAPs_Results/Results_Baseline_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

df_combined = compile_aggregated_sims_data(filepath, combinations, name_add='Baseline_', scenario_name='Moderate', quantile=0.8)
df_combined.to_csv(filepath + 'df_combined_modcool_Fig7.csv')

# 3. dry scenario
filepath = '/Volumes/OneTouch/CAPs_Results/Results_Baseline_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

df_combined_cc = compile_aggregated_sims_data(filepath, combinations, name_add='Baseline_', scenario_name='Dry', quantile=0.8)
df_combined_cc.to_csv(filepath + 'df_combined_cc_Fig7.csv')


#%% Create scatter plot
markers = {'No Assistance': 'o', 'Income': 's', 'Fixed Dollar: $50': '^', 'Fixed Dollar: $100': '^', 'Fee': '>',
           'Volumetric: 55%': '*', 'Volumetric: 80%': '*'}
fig, ax = plt.subplots(figsize=(6, 5))
plt.plot([-0.5, 20], [2.5, 2.5], color='darkgrey', linestyle='--', linewidth=1.2)

f = 1.02
labels = ['No \nassistance', 'Income', 'Fixed: \n$50', 'Fixed: \n$100', 'Fee', 'Vol.: \n55%', 'Vol.: \n80%']
i = 0
colors_lines = ['darkgray', 'firebrick', 'indianred', 'indianred', 'darkgreen', 'mediumblue', 'mediumblue']
# try plotting all lines
for cat in df_combined['policy'].unique():
    print(cat)
    fx = 1.02
    fy = 1.02
    if cat == 'Income':
        fx = 0.8
        fy = 0.7
    if cat == 'Fixed Dollar: $100':
        fx = 1.04
        fy = 0.92
    if cat == 'Volumetric: 80%':
        fx = 0.96
        fy = 1.07
    # get minimum point
    subset_hist = df_combined_hist[df_combined_hist['policy'] == cat]
    min_idx = np.argmin(subset_hist['annual_avg_cost'] / 1e6 + subset_hist['AR_80perc'])
    min_point = (subset_hist['annual_avg_cost'].iloc[min_idx] / 1e6, subset_hist['AR_80perc'].iloc[min_idx])
    # get max point
    subset_cc = df_combined_cc[df_combined_cc['policy'] == cat]
    max_idx = np.argmax(subset_cc['annual_avg_cost'] / 1e6 + subset_cc['AR_80perc'])
    max_point = (subset_cc['annual_avg_cost'].iloc[max_idx] / 1e6, subset_cc['AR_80perc'].iloc[max_idx])
    print('min point: {}, max point: {}'.format(min_point, max_point))
    if cat == 'Fixed Dollar: $100':
        subset_modcool = df_combined[df_combined['policy'] == cat]
        subset_all = pd.concat([subset_hist, subset_cc, subset_modcool])
        print('fixed dollar')
        # 2nd degree polynomial
        coeffs = np.polyfit(subset_all['annual_avg_cost'] / 1e6, subset_all['AR_80perc'], deg=2)
        poly_eq = np.poly1d(coeffs)
        # generate fitted vals
        x_fit = np.linspace(min(subset_all['annual_avg_cost']) / 1e6, max(subset_all['annual_avg_cost']) / 1e6, 100)
        y_fit = poly_eq(x_fit)
        plt.plot(x_fit, y_fit, '-', color=colors_lines[i], linewidth=1.3, alpha=0.7)
    else:
        # plot line
        plt.plot([min_point[0], max_point[0]], [min_point[1], max_point[1]], '-', color=colors_lines[i], linewidth=1.3,
                 alpha=0.7)
    # add label
    plt.text(max_point[0] * fx, max_point[1] * fy, labels[i], color=colors_lines[i], fontsize=11)
    i += 1

# mod, cool
for cat in df_combined['policy'].unique():
    subset = df_combined[df_combined['policy'] == cat]
    plt.scatter(subset['annual_avg_cost'] / 1e6, subset['AR_80perc'], s=20,
                color='dodgerblue', marker=markers[cat], alpha=0.7, edgecolors='navy', linewidths=0.4)

# dry, cool
for cat in df_combined_cc['policy'].unique():
    subset = df_combined_cc[df_combined_cc['policy'] == cat]
    plt.scatter(subset['annual_avg_cost'] / 1e6, subset['AR_80perc'], s=20,
                color='gold', marker=markers[cat], alpha=0.7, edgecolors='darkgoldenrod', linewidths=0.4)

# current conditions
for cat in df_combined_hist['policy'].unique():
    subset = df_combined_hist[df_combined_hist['policy'] == cat]
    plt.scatter(subset['annual_avg_cost'] / 1e6, subset['AR_80perc'], s=20,
                color='salmon', marker=markers[cat], alpha=0.7, edgecolors='darkred', linewidths=0.4)

# labels
plt.xlim(-0.5, 20)
plt.ylim(0, 15)
plt.xticks(np.arange(0, 21, 4), fontsize=11)
plt.yticks(np.arange(0, 16, 3), fontsize=11)
plt.xticks(fontsize=11)
plt.yticks(fontsize=11)
plt.xlabel('Average Annual Assistance Cost ($M)', fontsize=12)
plt.ylabel('80th percentile AR (% of bill / income)', fontsize=12)
plt.grid(True, alpha=0.5, color='silver')

# --- Custom Legend ---
# Create legend elements
marker_labels = ["No Assistance", "Income", "Fixed Dollar", "Fee", "Volumetric"]
color_list = ['salmon', 'dodgerblue', 'gold']
edgecolor_list = ['darkred', 'navy', 'darkgoldenrod']
color_labels = ["Baseline", "Moderate Climate \nwith Adaptation", "Dry Climate \nwith Adaptation"]
color_patches = [mpatches.Patch(facecolor=c, edgecolor=e, linewidth=1, label=l) for c, l, e in
                 zip(color_list, color_labels, edgecolor_list)]
shape_labels = ['No Assistance', 'Income', 'Fixed Dollar', 'Fee', 'Volumetric']
shape_list = ['o', 's', '^', '>', '*']
# Create custom legend elements
marker_size_list = [6, 6, 6, 6, 8]
shape_elements = [
    Line2D([0], [0], marker=shape, linestyle='None', label=label,
           markerfacecolor='gray', markeredgecolor='black', markersize=size)
    for shape, label, size in zip(shape_list, shape_labels, marker_size_list)
]

# Add legend to plot
legend2 = ax.legend(handles=shape_elements, bbox_to_anchor=(0.65, 1), loc="upper right", fontsize=9, frameon=False)
ax.add_artist(legend2)
plt.legend(handles=color_patches, bbox_to_anchor=(1.01, 1), loc="upper right", fontsize=9, frameon=False)

plt.savefig('../../outputs/Figures/explanatory/Figure7.jpg',
            bbox_inches='tight', dpi=300)
plt.show()