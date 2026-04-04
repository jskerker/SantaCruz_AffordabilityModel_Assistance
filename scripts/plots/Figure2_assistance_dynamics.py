#%% import packages
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.lines as mlines
import itertools
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")


#%% define functions
# function to add desal plan, deploy, and ramp down lines to time series plot
def add_desal_labels(ax, y_min, y_max, df_time_tracker):
    for i in range(len(df_time_tracker)):
        ax.plot([df_time_tracker['plan_date'].iloc[i], df_time_tracker['plan_date'].iloc[i]], [y_min, y_max],
                color='darkgray', linestyle=':', label='desal plan date')
        ax.plot([df_time_tracker['deploy_date'].iloc[i], df_time_tracker['deploy_date'].iloc[i]], [y_min, y_max],
                color='gray', linestyle=':', label='deploy date')
        ax.plot([df_time_tracker['ramp_down_date'].iloc[i], df_time_tracker['ramp_down_date'].iloc[i]], [y_min, y_max],
                color='black', linestyle=':', label='ramp down date')
        ax.axvspan(df_time_tracker['deploy_date'].iloc[i], df_time_tracker['ramp_down_date'].iloc[i], alpha=0.3,
                   color='lightgray')
    ax.set_ylim(y_min, y_max)


# function to add desal plan, deploy, and ramp down lines to time series plot- year
def add_desal_labels_year(ax, y_min, y_max, df_time_tracker):
    for i in range(len(df_time_tracker)):
        ax.plot([df_time_tracker['plan_year'].iloc[i], df_time_tracker['plan_year'].iloc[i]], [y_min, y_max],
                color='darkgray', linestyle=':')
        ax.plot([df_time_tracker['deploy_year'].iloc[i], df_time_tracker['deploy_year'].iloc[i]], [y_min, y_max],
                color='gray', linestyle=':')
        ax.plot([df_time_tracker['ramp_down_year'].iloc[i], df_time_tracker['ramp_down_year'].iloc[i]], [y_min, y_max],
                color='black', linestyle=':')
        ax.axvspan(df_time_tracker['deploy_year'].iloc[i], df_time_tracker['ramp_down_year'].iloc[i], alpha=0.3,
                   color='lightgray')
    ax.set_ylim(y_min, y_max)


# function to process annual data for a single account
def get_annual_data_random_acct(df, acct):
    # get data for random account
    df_filter = df[df['account'] == acct]

    # add water year column
    df_filter['Water_Year'] = df_filter['Date'].dt.year + (df_filter['Date'].dt.month >= 10).astype(int)

    # get annual values
    df_annual = df_filter.groupby('Water_Year', as_index=False).agg({
        'mapped_income': 'mean',
        'demand': 'mean',
        'totalWaterCosts': 'mean',
        'does_acct_get_assistance?': 'mean',
        # 'totalWaterCosts': 'sum',
        'AR': 'mean',
        'max_affordable_price': 'mean',
        'unafford_bill_difference': 'mean',
        'totalWaterCostsAssist_income': 'mean',
        'AR_assist_income': 'mean'
    })
    return df_annual


# process df_time_tracker
def process_time_tracker(df_time_tracker):
    # convert columns to datetime
    df_time_tracker['plan_date'] = pd.to_datetime(df_time_tracker['plan_date'])
    df_time_tracker['deploy_date'] = pd.to_datetime(df_time_tracker['deploy_date'])
    df_time_tracker['payback_date'] = pd.to_datetime(df_time_tracker['payback_date'])
    df_time_tracker['ramp_down_date'] = pd.to_datetime(df_time_tracker['ramp_down_date'])

    # get years instead of dates
    df_time_tracker['plan_year'] = df_time_tracker['plan_date'].dt.year
    df_time_tracker['deploy_year'] = df_time_tracker['deploy_date'].dt.year
    df_time_tracker['payback_year'] = df_time_tracker['payback_date'].dt.year
    df_time_tracker['ramp_down_year'] = df_time_tracker['ramp_down_date'].dt.year
    return df_time_tracker

print('import packages & define functions')


#%% import and process data
# import data- mod, cool 3449
filepath = '../../results/CAPs_Results/'
real_All = [3449]  # , 3515, 3574, 4211, 4373, 4937] 1270, 1956, 1987, 2770,
dT_All = [0]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)
    # get household level data
    df = pd.read_parquet(
        filepath + 'df_assisted_bill_Multi_P{}T{}_dCV{}_real{}_demand{}.parquet'.format(combo[2], combo[1], combo[3],
                                                                                        combo[0], combo[4]))
    df['Date'] = pd.to_datetime(df['Date'])

    # get time_tracker data
    df_time_tracker = pd.read_csv(
        filepath + 'df_time_tracker_Multi_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3],
                                                                                   combo[0], combo[4]))
    df_time_tracker = process_time_tracker(df_time_tracker)


#%% get a random account and process data from monthly to annual (by water year)

# Filter rows where 'mapped_income' <= 55k and select a random value from 'account'
#acct_med = df[df['mapped_income'] == 54999.5]['account'].sample(1).iloc[0]
acct_assist = 12063
print('random account: ', acct_assist)
df_annual_assist = get_annual_data_random_acct(df, acct_assist)

# get second random acct
acct_high = 3217 # df[df['mapped_income'] > 90000]['account'].sample(1).iloc[0] #3217
print('account high: ', acct_high)
df_annual_NoAssist = get_annual_data_random_acct(df, acct_high)
print(df_annual_NoAssist)


#%% plot figure

ft1 = 11  # 10.5
fig = plt.figure(figsize=(9, 12))
gs = gridspec.GridSpec(4, 3, height_ratios=[2, 2, 0.75, 2.75], width_ratios=[2, 0.75, 0.75], wspace=0.25, hspace=0.3)

# time series plot for bills
ax0 = fig.add_subplot(gs[0, 0:3])
y_min = 0
y_max = 220
add_desal_labels_year(ax0, y_min, y_max, df_time_tracker)
ax0.plot(df_annual_NoAssist['Water_Year'], df_annual_NoAssist['totalWaterCosts'], linewidth=1.6, color='salmon')
ax0.plot(df_annual_assist['Water_Year'], df_annual_assist['totalWaterCosts'], linewidth=1.6, color='navy')
ax0.plot(df_annual_assist['Water_Year'], df_annual_assist['totalWaterCostsAssist_income'], linewidth=1.6, color='navy',
         linestyle='--')
# ax0.plot(df_annual['Water_Year'], df_annual['unafford_bill_difference'], linewidth=1.5, color='salmon')
ax0.set_ylabel('Bill ($/mo)', fontsize=ft1)
ax0.set_xlim(2020, 2070)
ax0.set_ylim(y_min, y_max)
ax0.set_xticklabels(np.arange(2020, 2071, 10), fontsize=ft1)
ax0.set_yticklabels(np.arange(0, 225, 50), fontsize=ft1)
ax0.set_title('Water Bills', fontweight='bold', fontsize=ft1 + 1)

# custom legend
legend_handles = [
    mlines.Line2D([], [], color='salmon', linewidth=1.6, linestyle='-', label='Household A (High Income)'),
    mlines.Line2D([], [], color='navy', linewidth=1.6, linestyle='-', label='Household B (Low Income)'),
    mlines.Line2D([], [], color='gray', linewidth=1.6, linestyle='--', label='With Assistance')]
ax0.legend(handles=legend_handles, bbox_to_anchor=(0.0, -0.02), loc="lower left", fontsize=ft1, frameon=False)
# add text
ax0.text(2044.5, 184, 'Plan \ninfrastructure', fontstyle='italic', fontsize=ft1)
ax0.text(2054.5, 201, 'Deploy infrastructure', fontstyle='italic', fontsize=ft1)

# time series plot for ARs
ax1 = fig.add_subplot(gs[1, 0:3])
y_min = 0
y_max = 5
add_desal_labels_year(ax1, y_min, y_max, df_time_tracker)
ax1.plot([2020, 2070], [2.5, 2.5], color='gray', linewidth=1.2, linestyle='-.')
ax1.plot(df_annual_assist['Water_Year'], df_annual_assist['AR_assist_income'], linewidth=1.6, color='navy',
         linestyle='--')
ax1.plot(df_annual_assist['Water_Year'], df_annual_assist['AR'], linewidth=1.6, color='navy')
ax1.plot(df_annual_NoAssist['Water_Year'], df_annual_NoAssist['AR'], linewidth=1.6, color='salmon')

ax1.set_xlabel('Time', fontsize=ft1)
ax1.set_ylabel('AR (% of bill / income)', fontsize=ft1)
ax1.text(2021, 2.65, 'EPA affordability threshold', fontsize=ft1, fontstyle='italic')
ax1.set_xlim(2020, 2070)
ax1.set_ylim(y_min, y_max)
ax1.set_xticklabels(np.arange(2020, 2071, 10), fontsize=ft1)
ax1.set_yticklabels(np.arange(0, 6, 1), fontsize=ft1)
ax1.set_title('Affordability Burdens', fontweight='bold', fontsize=ft1 + 1)

# scatter plot with sample of HHs w/ and w/o assistance
ax2 = fig.add_subplot(gs[3, 0])
cols = ['unafford_bill_difference', 'totalWaterCosts', 'AR', 'totalWaterCostsAssist_income', 'AR_assist_income']
df = df[cols]
df_sample = df.sample(n=500, random_state=19)
df_sample_assist = df_sample[df_sample['unafford_bill_difference'] > 0]
ax2.plot([0, 300], [2.5, 2.5], color='gray', linestyle='--', linewidth=1.5)
ax2.scatter(df_sample['totalWaterCosts'], df_sample['AR'], s=10, alpha=0.7, color='gold')
# ax0.scatter(df_sample_assist['totalWaterCostsAssist_income'], df_sample_assist['AR_assist_income'], marker='^', s=10, alpha=1, color='dodgerblue')
ax2.scatter(df_sample['totalWaterCostsAssist_income'], df_sample['AR_assist_income'], s=10, alpha=0.4,
            color='olivedrab')
ax2.set_xlabel('Bill ($/mo)', fontsize=ft1)
ax2.set_ylabel('AR (% of bill / income)', fontsize=ft1)
ax2.set_xlim(0, 300)
ax2.set_ylim(-0.5, 10)
ax2.set_xticklabels(np.arange(0, 301, 50), fontsize=ft1)
ax2.set_yticks(np.arange(0, 11, 2))
ax2.set_yticklabels(np.arange(0, 11, 2), fontsize=ft1)
ax2.grid(True)
left, bottom, width, height = ax2.get_position().bounds
ax2.set_position([left, bottom + 0.04, width, height])
# custom legend
marker_handles = [mlines.Line2D([], [], color='gold', marker='o', linestyle='None', alpha=0.7, markersize=4,
                                label='Before Assistance'),
                  mlines.Line2D([], [], color='olivedrab', marker='o', linestyle='None', alpha=0.4, markersize=4,
                                label='With Assistance')]

# Add legend to plot
ax2.legend(handles=marker_handles, bbox_to_anchor=(1.58, 1.05), loc="upper right", fontsize=ft1, frameon=False,
           handletextpad=0.4)
ax2.set_title('500 Sample Households', fontweight='bold', fontsize=ft1 + 1)

# kde plot for ARs
ax3 = fig.add_subplot(gs[3, 1])
bw = 1.2
sns.kdeplot(data=df, y='AR', ax=ax3, color='gold', alpha=0.8, linewidth=1.8, label='Before assistance', bw_adjust=bw)
sns.kdeplot(data=df, y='AR_assist_income', ax=ax3, color='olivedrab', alpha=0.8, linewidth=1.8, label='With assistance',
            bw_adjust=bw)
ax3.set_ylim(-0.5, 10)
ax3.set_yticks([])
ax3.set_xlim(-0.2, 2.5)
ax3.set_xticks([])
ax3.set_ylabel('')
ax3.set_xlabel('')
# set background to be white
ax3.set_facecolor('white')  # Sets background to white
ax3.patch.set_visible(False)  # Hides the background completely
ax3.grid(False)  # remove grid lines
# move subplot
left, bottom, width, height = ax3.get_position().bounds
ax3.set_position([left - 0.045, bottom + 0.04, width, height])
for spine in ax3.spines.values():  # get rid of spines (borders)
    spine.set_visible(False)

# kde plot for bills
ax4 = fig.add_subplot(gs[2, 0])
bw = 2.5  # 2
sns.kdeplot(data=df, x='totalWaterCosts', ax=ax4, color='gold', alpha=0.8, linewidth=1.8, label='Before Assistance',
            bw_adjust=bw)
sns.kdeplot(data=df, x='totalWaterCostsAssist_income', ax=ax4, color='olivedrab', alpha=0.8, linewidth=1.8,
            label='With Assistance', bw_adjust=bw)
ax4.set_yticks([])
ax4.set_xlim(0, 300)
ax4.set_xticks([])
ax4.set_ylabel('')
ax4.set_xlabel('')
# set background to be white
ax4.set_facecolor('white')  # Sets background to white
ax4.patch.set_visible(False)  # Hides the background completely
ax4.grid(False)  # remove grid lines
# move subplot
left, bottom, width, height = ax4.get_position().bounds
ax4.set_position([left, bottom + 0.015, width, height])
for spine in ax4.spines.values():  # get rid of spines (borders)
    spine.set_visible(False)

# add labels
ax2.text(5, 32.1, 'a', fontsize=18, fontweight='bold')
ax2.text(5, 22.1, 'b', fontsize=18, fontweight='bold')
ax2.text(5, 9.3, 'c', fontsize=18, fontweight='bold')

plt.savefig('../../outputs/Figures/explanatory/Figure2.png', dpi=300, bbox_inches='tight')
plt.show()