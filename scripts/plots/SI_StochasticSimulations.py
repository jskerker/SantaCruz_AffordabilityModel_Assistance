#%% Import packages
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import itertools
import random
from matplotlib.lines import Line2D
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

#%% Import subset of stochastic climate simulations
# mod, cool combinations
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
combinations_mod = list(itertools.product(real_All, dT_All, dP_All, dCV_All))

dT_All = [4, 5]
dP_All = [80]
dCV_All = [1.2]
combinations_cc = list(itertools.product(real_All, dT_All, dP_All, dCV_All))

# filepath
filepath = '../../../Santa_Cruz_WRM_updated/data/input_climate_stress_test/FLOW/'


#%% Create two-panel time series plot
fig, ax = plt.subplots(figsize=(10, 8), nrows=2, ncols=1)
fig.subplots_adjust(hspace=0.3)

# randomly sample combinations
random.seed(19)
samples = 2
sampled_combos_mod = random.sample(combinations_mod, samples)
sampled_combos_cc = random.sample(combinations_cc, samples)
yrs = 10

### subplot 1: sample of annual data ###
# moderate
for combo in sampled_combos_mod:
    # Read the CSV into a DataFrame
    df = pd.read_csv(filepath + 'FLOW_P{}T{}_R{}_dCV={}.csv'.format(combo[2], combo[1], combo[0], combo[3]))

    # Set the date to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # aggregate annually
    df_annual = df.resample('Y').mean()
    ax[0].plot(df_annual['BIGTREES_Na'], color='dodgerblue', linewidth=0.8)

for combo in sampled_combos_cc:
    # Read the CSV into a DataFrame
    df = pd.read_csv(filepath + 'FLOW_P{}T{}_R{}_dCV={}.csv'.format(combo[2], combo[1], combo[0], combo[3]))

    # Set the date to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # aggregate annually
    df_annual = df.resample('Y').mean()
    ax[0].plot(df_annual['BIGTREES_Na'], color='salmon', linewidth=0.8)

ax[0].set_xlim([datetime(2019, 10, 1), datetime(2100, 12, 31)])
ax[0].set_ylabel('Streamflow (cfs)', fontsize=12)
ax[0].set_title('Annually-Averaged Daily Streamflow on the San Lorenzo River', fontsize=12)
ax[0].grid(True, alpha=0.27)

# Custom legend elements
custom_lines = [
    Line2D([0], [0], color='dodgerblue', lw=0.8, label='Moderate Climate'),
    Line2D([0], [0], color='salmon', lw=0.8, label='Dry Climate')
]
# Add legend
ax[0].legend(handles=custom_lines, title='Scenario', fontsize=10, title_fontsize=10, loc='upper right')

### subplot 2: sample of moving average data ###
# moderate
for combo in sampled_combos_mod:
    # Read the CSV into a DataFrame
    df = pd.read_csv(filepath + 'FLOW_P{}T{}_R{}_dCV={}.csv'.format(combo[2], combo[1], combo[0], combo[3]))

    # Set the date to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # aggregate annually
    df_annual = df.resample('Y').mean()
    df_annual['mov_avg'] = df_annual['BIGTREES_Na'].rolling(window=yrs, center=True).mean()
    ax[1].plot(df_annual['mov_avg'], color='dodgerblue', linewidth=0.8)

for combo in sampled_combos_cc:
    # Read the CSV into a DataFrame
    df = pd.read_csv(filepath + 'FLOW_P{}T{}_R{}_dCV={}.csv'.format(combo[2], combo[1], combo[0], combo[3]))

    # Set the date to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # aggregate annually
    df_annual = df.resample('Y').mean()
    df_annual['mov_avg'] = df_annual['BIGTREES_Na'].rolling(window=yrs, center=True).mean()
    ax[1].plot(df_annual['mov_avg'], color='salmon', linewidth=0.8)

ax[1].set_xlim([datetime(2019, 10, 1), datetime(2100, 12, 31)])
ax[1].set_xlabel('Year', fontsize=12)
ax[1].set_ylabel('Streamflow (cfs)', fontsize=12)
ax[1].set_title('10-Year Moving Average of Annually-Averaged Daily Streamflow on the San Lorenzo River', fontsize=12)
ax[1].grid(True, alpha=0.3)

plt.savefig('../../outputs/Figures/SI/SI_TimeSeries_Streamflow.png', dpi=300, bbox_inches='tight') # transparent=True
plt.show()