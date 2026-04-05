#%% import packages and define functions
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import itertools
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")
import os
import sys
import processing_functions_March2025 as pf
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings("ignore")
sys.path.append('../scripts')

# function to process monthly data with filtering for the max rates
def process_monthly_with_dates_filter(filepath, combo, name_add, ie):
    column_names = ['Date', 'tot_assist_income', 'Count']
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates_IE2(filepath, combo, name_add, ie)
    # print(df_max_rate_dates)
    df = pd.read_csv(
        filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, combo[2], combo[1],
                                                                                     combo[3], combo[0], combo[4], ie))
    df = df[column_names]
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]

    df_filter['real'] = combo[0]
    df_filter['dT'] = combo[1]
    df_filter['dP'] = combo[2]
    df_filter['dCV'] = combo[3]
    df_filter['demand'] = combo[4]
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
    # find row where col value is closest to avg
    closest_row_idx = (df_cost[col_name] - stat).abs().idxmin()

    return df_cost.loc[closest_row_idx]  # retrieve full row

# function to get household counts by 4 income groups for hhs requiring/not assistance
def get_hh_counts_by_income_group(filepath, df_avg, name_add, ie):
    columns = ['Date', 'account', 'does_acct_get_assistance?']
    # 2. load household assistance data for that scenario and realization
    real = df_avg.loc['real']
    dT = df_avg.loc['dT']
    dP = df_avg.loc['dP']
    dCV = df_avg.loc['dCV']
    demand = df_avg.loc['demand']
    df_hh = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.parquet'.format(name_add, dP, dT, dCV, real,
                                                                                    demand, ie), columns=columns)
    df_hh['Date'] = pd.to_datetime(df_hh['Date'])

    # 3. filter data by date
    df_hh_filter = df_hh[df_hh['Date'].isin([df_avg.loc['Date']])]
    print(df_hh_filter)

    # 4. Merge with income data
    # including: a) create 4 income groups
    df_income = pd.read_csv('../../data/dcc_data/resampled_income_data.csv')
    df_income = df_income[['account', 'map_inc_{}'.format(ie)]]
    df_income['mapped_income'] = df_income['map_inc_{}'.format(ie)]

    # Define conditions
    conditions = [
        df_income['mapped_income'] < 40000,
        (df_income['mapped_income'] >= 40000) & (df_income['mapped_income'] < 87499.5),
        (df_income['mapped_income'] >= 87499.5) & (df_income['mapped_income'] < 174999.5),
        df_income['mapped_income'] >= 174999.5
    ]
    # Define corresponding labels
    labels = ['Low', 'Below MHI', 'MHI to High', 'High']
    # Assign values based on conditions
    df_income['income_group'] = np.select(conditions, labels, default='Unassigned')

    # how many unassigned values are there?
    count = (df_income["income_group"] == 'Unassigned').sum()
    print('how many unassigned values are there? {}'.format(count))
    # merge dataframes
    df_merge = pd.merge(df_hh_filter, df_income, on='account', how='left')

    # 5. figure out how to subset data by if assistance needed and income group
    df_counts = df_merge.groupby(['does_acct_get_assistance?', 'income_group']).size().unstack(fill_value=0)
    df_counts = df_counts[['Low', 'Below MHI', 'MHI to High', 'High']]
    print(df_counts)
    arr_hist = np.array([df_counts.loc[1, 'Low'], df_counts.loc[1, 'Below MHI'], df_counts.loc[1, 'MHI to High'],
                         df_counts.loc[1, 'High'], df_counts.loc[0, 'Low'], df_counts.loc[0, 'Below MHI'],
                         df_counts.loc[0, 'MHI to High'], df_counts.loc[0, 'High']])
    arr_col = arr_hist[:, np.newaxis]

    return arr_col, df_merge, [real, dT, dP, dCV, demand]


# for each scenario, extract the data from that month
def get_accts_assistance_for_baseline(df_stat, filepath, name_add, dP, dCV, demand, ie):
    columns = ['Date', 'account', 'totalWaterCosts', 'AR', 'does_acct_get_assistance?', 'totalWaterCostsAssist_income',
               'unafford_bill_difference', 'AR_assist_income']

    # get data from df_stat
    real = df_stat.loc['real']
    dT = df_stat.loc['dT']
    date = df_stat.loc['Date']
    df_hh = pd.read_parquet(
        filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.parquet'.format(name_add, dP, dT, dCV, real,
                                                                                    demand, ie), columns=columns)  #
    df_hh_filter = df_hh[df_hh['Date'] == date]

    # get amount of assistance
    assistance = df_hh_filter['unafford_bill_difference'].sum()

    # get accounts getting assistance
    df_accts = df_hh_filter.loc[df_hh_filter['does_acct_get_assistance?'] == 1, 'account']
    return assistance, df_accts

print('import packages')

#%% load cost data
# import all monthly assistance data and filter by periods with max rate dates
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
    df_filter = process_monthly_with_dates_filter(filepath, combo, name_add, ie)
    df_hist_cost = pd.concat([df_hist_cost, df_filter], ignore_index=True)

    # modcool data
    name_add = 'Baseline_IE_'
    df_filter = process_monthly_with_dates_filter(filepath, combo, name_add, ie)
    df_modcool_cost = pd.concat([df_modcool_cost, df_filter], ignore_index=True)

# climate change
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)

    # dry, hot
    df_filter = process_monthly_with_dates_filter(filepath, combo, name_add, ie)
    df_cc_cost = pd.concat([df_cc_cost, df_filter], ignore_index=True)

#%% get data for bar plots
# 1. Average: get stastic values and corresponding rows for all 3 scenarios
col_name = 'tot_assist_income'
stat_name = 'mean'

df_hist_avg = get_closest_row_from_data(df_hist_cost, col_name, stat_name)
df_modcool_avg = get_closest_row_from_data(df_modcool_cost, col_name, stat_name)
df_cc_avg = get_closest_row_from_data(df_cc_cost, col_name, stat_name)

print(df_modcool_avg)
print('\n')

#print(df_hist_avg)
# baseline
name_add = 'Baseline_IE_NoInf_'
arr_hist, df_merge_hist, list_combo = get_hh_counts_by_income_group(filepath, df_hist_avg, name_add, ie)

# modcool
name_add = 'Baseline_IE_'
arr_modcool, df_merge_modcool, list_combo_mc = get_hh_counts_by_income_group(filepath, df_modcool_avg, name_add, ie)

# dry
name_add = 'Baseline_IE_'
arr_cc, df_merge_cc, list_combo_cc = get_hh_counts_by_income_group(filepath, df_cc_avg, name_add, ie)

#print(arr_cc)
arr_combined = np.hstack((arr_hist, arr_modcool, arr_cc))

#%% import household assistance data for dry realization used above
columns = ['Date', 'account', 'does_acct_get_assistance?']
df_avg = df_modcool_avg.copy()
print('dataframe with average values: \n', df_avg)
# 2. load household assistance data for that scenario and realization
real = df_avg.loc['real']
dT = df_avg.loc['dT']
dP = df_avg.loc['dP']
dCV = df_avg.loc['dCV']
demand = df_avg.loc['demand']
df_hh = pd.read_parquet(
    filepath + 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.parquet'.format(name_add, dP, dT, dCV, real, demand, ie),
    columns=columns)
df_hh['Date'] = pd.to_datetime(df_hh['Date'])

# 4. Merge with income data
# including: a) create 4 income groups
df_income = pd.read_csv('../../data/dcc_data/resampled_income_data.csv')
df_income = df_income[['account', 'map_inc_{}'.format(ie)]]
df_income['mapped_income'] = df_income['map_inc_{}'.format(ie)]

# Define conditions
conditions = [
    df_income['mapped_income'] < 40000,
    (df_income['mapped_income'] >= 40000) & (df_income['mapped_income'] < 87499.5),
    (df_income['mapped_income'] >= 87499.5) & (df_income['mapped_income'] < 174999.5),
    df_income['mapped_income'] >= 174999.5
]
# Define corresponding labels
labels = ['Low', 'Below MHI', 'MHI to High', 'High']
# Assign values based on conditions
df_income['income_group'] = np.select(conditions, labels, default='Unassigned')
count = (df_income["income_group"] == 'Unassigned').sum()
print('how many unassigned values are there? {}'.format(count))
# merge dataframes
df_merge = pd.merge(df_hh, df_income, on='account', how='left')

# filter accounts getting assistance
df_assistance = df_merge[df_merge['does_acct_get_assistance?'] == 1]

# Count occurrences of income_group for each Date
df_counts = df_assistance.groupby(["Date", "income_group"]).size().reset_index(name="count")

print(df_counts)

# import df time tracker dataframe
df_time_tracker = pd.read_csv(filepath + 'df_time_tracker_{}P{}T{}_dCV{}_real{}_demand{}_IE{}.csv'.format(name_add, dP, dT, dCV, real, demand, ie))
print(df_time_tracker.loc[0, 'deploy_date'])

#%% create figure
# create updated bar plot
custom_colors = ['dodgerblue', 'gold', 'olivedrab', 'salmon', 'dodgerblue', 'gold', 'olivedrab', 'salmon']
# Define hatching patterns (apply to selected bars)
hatch_patterns = ['', '', '', '', 'x', 'x', 'x', 'x']  # Every second bar has hatching
alpha_values = [1.0, 1.0, 1.0, 1.0, 0.8, 0.8, 0.8, 0.8]
categories = ['Baseline', 'Moderate', 'Dry']
ft = 11
wd = 0.7
# create figure
fig = plt.figure(figsize=(10, 4))
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], wspace=0.2)

### first subplot: bar plots ###
ax0 = fig.add_subplot(gs[0, 0])
bottom = np.zeros(len(categories))  # Initialize bottom at 0 for stacking
for i in range(arr_combined.shape[0]):
    ax0.bar(categories, arr_combined[i, :], bottom=bottom, width=wd, color=custom_colors[i], hatch=hatch_patterns[i], alpha=alpha_values[i])
    bottom += arr_combined[i, :]

# add labels
ax0.set_xlabel('Climate Scenario', fontsize=ft+1)
ax0.set_ylabel('Number of Households', fontsize=ft+1)
ax0.set_xticks(categories)
ax0.set_xticklabels(categories, fontsize=ft+1)
ax0.set_yticks(np.arange(0, 20001, 4000))
ax0.set_yticklabels(np.arange(0, 20001, 4000), fontsize=ft)
ax0.set_xlim(-0.75, 2.75)
ax0.set_ylim(0, 22500)

ax0.set_title('n = 21,370 households', fontweight='bold', fontsize=ft+1)

### second subplot: timeseries ###
ax1 = fig.add_subplot(gs[0, 1])
df_pivot = df_counts.pivot(index="Date", columns="income_group", values="count").fillna(0)
df_pivot = df_pivot[['Low', 'Below MHI', 'MHI to High', 'High']]
ft = 11
# Sort by date (important for plotting)
df_pivot = df_pivot.sort_index()

# Create stacked area chart
ax1.stackplot(df_pivot.index, df_pivot.T, labels=df_pivot.columns, alpha=1.0, colors=custom_colors)

# add line for deploy date
deploy_date = pd.to_datetime(df_time_tracker.loc[0, 'deploy_date'])
deploy_year = deploy_date.year
ax1.plot([deploy_date, deploy_date], [0, 8000], linestyle='--', color='black', linewidth=1.8)

# Formatting
ax1.set_xlabel("Date", fontsize=ft+1)
#ax1.set_ylabel("Number of Households", fontsize=ft+1)
# Set major ticks to show every year
ax1.xaxis.set_major_locator(mdates.YearLocator(1))  # Change to 2 for every other year
# Format tick labels to show only the year
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
# Adjust tick label size and rotation
ax1.tick_params(axis="x", labelsize=ft+1, rotation=0)
ax1.set_xlim(pd.to_datetime('{}-01-01'.format(deploy_year-2)), pd.to_datetime('{}-01-01'.format(deploy_year+4)))
ax1.set_ylim(0, 8000)
ax1.set_yticks(np.arange(0, 8001, 2000))
ax1.set_yticklabels(np.arange(0, 8001, 2000), fontsize=ft)

# create custom legend
# Custom Legend with Patches
legend_patches = [
    mpatches.Patch(color=custom_colors[0], label='Low'),
    mpatches.Patch(color=custom_colors[1], label='Below MHI'),
    mpatches.Patch(color=custom_colors[2], label='MHI to High'),
    mpatches.Patch(color=custom_colors[3], label='High'),
    mpatches.Patch(facecolor='white', edgecolor='black', hatch='x', label='No Assistance')
]

# Add legend
ax1.legend(handles=legend_patches, loc="lower right", bbox_to_anchor=(1.0, 0.0), fontsize=ft-0.5)

# text
ax1.text(pd.to_datetime('{}-12-01'.format(deploy_year)), 7500, 'Deploy infrastructure', fontsize=ft-1, fontstyle='italic')
ax1.set_title('Households Requiring Assistance', fontweight='bold', fontsize=ft+1)

# add text for figure labels
ax1.text(pd.to_datetime('{}-11-25'.format(deploy_year-10)), 7400, 'a', fontsize=18, fontweight='bold')
ax1.text(pd.to_datetime('{}-02-10'.format(deploy_year-2)), 7300, 'b', fontsize=18, fontweight='bold')

plt.savefig('../../outputs/Figures/Figure5_IE_Bars_TimeSeries.png', dpi=300, bbox_inches='tight')

#%% print out statistics
# get percentage of households receiving assistance in each group
print('LOW INCOME')
perc_baseline = arr_combined[0,0] / (arr_combined[0,0]+arr_combined[4, 0]) * 100
perc_cc = arr_combined[0,2] / (arr_combined[0,2]+arr_combined[4, 2]) * 100
print('baseline: {}%, CC: {}'.format(perc_baseline, perc_cc))

print('BELOW MHI')
perc_baseline = arr_combined[1,0] / (arr_combined[1,0]+arr_combined[5, 0]) * 100
perc_cc = arr_combined[1,2] / (arr_combined[1,2]+arr_combined[5, 2]) * 100
print('baseline: {}%, CC: {}'.format(perc_baseline, perc_cc))

print('MHI TO HIGH')
perc_baseline = arr_combined[2,0] / (arr_combined[2,0]+arr_combined[6, 0]) * 100
perc_cc = arr_combined[2,2] / (arr_combined[2,2]+arr_combined[6, 2]) * 100
print('baseline: {}%, CC: {}'.format(perc_baseline, perc_cc))

print('HIGH')
perc_baseline = arr_combined[3,0] / (arr_combined[3,0]+arr_combined[7, 0]) * 100
perc_cc = arr_combined[3,2] / (arr_combined[3,2]+arr_combined[7, 2]) * 100
print('baseline: {}%, CC: {}'.format(perc_baseline, perc_cc))