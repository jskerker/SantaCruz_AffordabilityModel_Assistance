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
import os
import warnings
warnings.filterwarnings("ignore")
from Setup_SCWSM_Option_Analysis_CST import simSetup
print('import packages')


#%% Import inf count and average assistance cost- modcool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_updated_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))
inf_count = []

for combo in combinations:
    print(combo)
    # count number of inf options
    df = pd.read_csv(filepath + 'df_time_tracker_Baseline_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3], combo[0], combo[4]))
    num_rows = len(df)

    # get avg assistance value
    df = pd.read_csv(filepath + 'df_monthly_assistance_Baseline_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3], combo[0], combo[4]))
    avg_assist = df['tot_assist_income'].sum()/50

    inf_count.append({'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4], 'inf_options': num_rows, 'avg_assist_annual': avg_assist})

df_inf_count = pd.DataFrame(inf_count)
print(df_inf_count)


#%% Import inf count and average assistance cost- dryhot
filepath = '/Volumes/OneTouch/CAPs_Results/Results_updated_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [4, 5]
dP_All = [80]
dCV_All = [1.2]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))
inf_count = []

for combo in combinations:
    print(combo)
    # count number of inf options
    df = pd.read_csv(filepath + 'df_time_tracker_Baseline_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3], combo[0], combo[4]))
    num_rows = len(df)

    # get avg assistance value
    df = pd.read_csv(filepath + 'df_monthly_assistance_Baseline_P{}T{}_dCV{}_real{}_demand{}.csv'.format(combo[2], combo[1], combo[3], combo[0], combo[4]))
    avg_assist = df['tot_assist_income'].sum()/50

    inf_count.append({'real': combo[0], 'dT': combo[1], 'dP': combo[2], 'dCV': combo[3], 'demand': combo[4], 'inf_options': num_rows, 'avg_assist_annual': avg_assist})

df_inf_count_cc = pd.DataFrame(inf_count)
print(df_inf_count_cc)

#%% Create scatter plot of data
plt.figure(figsize=(6, 4))
plt.scatter(df_inf_count['inf_options'], df_inf_count['avg_assist_annual']/1e6, color='dodgerblue', alpha=0.5, label='Moderate Climate')
plt.scatter(df_inf_count_cc['inf_options'], df_inf_count_cc['avg_assist_annual']/1e6, color='salmon', alpha=0.5, label='Dry Climate')

# add labels
leg = plt.legend(title='Scenario', loc='upper left', fontsize=10, title_fontsize=10, handletextpad=0.4)
plt.xlabel('Number of infrastructure options deployed', fontsize=12)
plt.ylabel('Average annual assistance ($M)', fontsize=12)
plt.xlim([-0.25, 3.25])
plt.xticks(range(0, 4), fontsize=11)
y_max = 8
plt.ylim([0, y_max])
plt.yticks(range(0, y_max+1, 2), fontsize=11)
plt.title('Scatter plot comparing average annual assistance \ncosts and amount of infrastructure deployed', fontsize=12)

plt.savefig('../../outputs/Figures/SI/SI_Scatter_Support_Fig3.png', dpi=300, bbox_inches='tight') # transparent=True
plt.show()