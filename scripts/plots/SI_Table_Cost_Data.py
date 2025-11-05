#%% Import packages & define functions
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
import processing_functions_March2025 as pf
warnings.filterwarnings("ignore")
import os
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.append('/Users/jenniferskerker/Documents/GradSchool/Research/Equity/Model/Santa_Cruz_WRM_Assistance/scripts')
from Setup_SCWSM_Option_Analysis_CST import simSetup
import sqlite3
import pickle

def pickleload(filename):
    """load previously saved python object from pickle (binary)
        Args:
             filename: filename as string where object previously saved to with pickle (e.g., sample.txt)
        Returns:
             obj: the previously saved python object
        """
    # read binary
    with open(filename, 'rb') as f:
        obj = pickle.load(f)

    return obj
def process_monthly_data_to_annual(df):
    # remove Water_Year 2021 data

    # aggregate data to annual
    # df_annual = df.groupby('Water_Year', as_index=False)[['tot_assist_income', 'tot_assist_fixedDollar', 'tot_assist_fee', 'tot_assist_vol']].sum()
    # df_annual = df.groupby('Water_Year')[['tot_assist_income', 'tot_assist_fixedDollar', 'tot_assist_fee', 'tot_assist_vol']].sum()

    df_annual_v2 = df.groupby('Water_Year').agg({
        'tot_assist_income': 'sum',
        'tot_assist_fixedDollar_$50': 'sum',
        'tot_assist_fixedDollar_$100': 'sum',
        'tot_assist_fee': 'sum',
        'tot_assist_vol_55%': 'sum',
        'tot_assist_vol_80%': 'sum',
        'Count': 'mean',
        'Water_Year': 'size'  # adds a count of entries per group
    }).rename(columns={'Water_Year': 'entry_count'}).reset_index()

    return df_annual_v2


def process_monthly_data_to_annual_dates_filter(filepath, combo, name_add):
    df_cashflow, max_rates, df_max_rate_dates = pf.get_max_rate_dates(filepath, combo, name_add)
    # print(df_max_rate_dates)
    df = pd.read_csv(
        filepath + 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, combo[2], combo[1],
                                                                                     combo[3], combo[0], combo[4]))
    df['Date'] = pd.to_datetime(df['Date'])
    df_filter = df[df['Date'].isin(df_max_rate_dates)]
    df_annual = process_monthly_data_to_annual(df_filter)
    df_annual = df_annual[df_annual['entry_count'] == 12]
    df_annual['real'] = combo[0]
    df_annual['dT'] = combo[1]
    df_annual['dP'] = combo[2]
    # print(df_annual)
    return df_annual

print('import packages & define functions')

#%% Import cost data
## Question 3: How much will this cost? ##
# import data
filepath = '/Volumes/OneTouch/CAPs_Results/Results_Baseline_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

df_hist = pd.DataFrame()
df_modcool = pd.DataFrame()
df_cc = pd.DataFrame()

for combo in combinations:
    print(combo)

    # current conditions data
    name_add = 'Baseline_NoInf_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_hist = pd.concat([df_hist, df_annual], ignore_index=True)

    # modcool data
    name_add = 'Baseline_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_modcool = pd.concat([df_modcool, df_annual], ignore_index=True)

# climate change
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

for combo in combinations:
    print(combo)

    # hot, dry
    name_add = 'Baseline_'
    df_annual = process_monthly_data_to_annual_dates_filter(filepath, combo, name_add)
    df_cc = pd.concat([df_cc, df_annual], ignore_index=True)

#%% Get total number of households
df = pd.read_parquet(filepath + 'df_assisted_bill_Baseline_P{}T{}_dCV{}_real{}_demand{}.parquet'.format(combo[2], combo[1], combo[3], combo[0], combo[4]))
num_HHs = df['account'].nunique()
print(num_HHs)

#%% Get average annual assistance costs
avg = df_cc.mean(axis=0)
# columns to modify
cols = ['tot_assist_income', 'tot_assist_fixedDollar_$50', 'tot_assist_fixedDollar_$100', 'tot_assist_fee', 'tot_assist_vol_55%', 'tot_assist_vol_80%']
for col in cols:
    avg[col] = avg[col]/1e6
    # calculate percent of baseline utility costs
    avg[col+'_percent'] = avg[col]/45.1 * 100

    # calculate approx fixed fees
    avg[col+'_addedFees_All'] = avg[col]*1e6/12/num_HHs
    avg[col+'_addedFees_Subset'] = avg[col]*1e6/12/(num_HHs-avg['Count'])

print(avg)

#%% Import water billing data
# set working directory
os.chdir('/Users/jenniferskerker/Documents/GradSchool/Research/Equity/Model/DCC_Demand_Estimation')

# define columns to import
csvpath = '/Users/jenniferskerker/Documents/GradSchool/Research/Equity/Model/DCC_Demand_Estimation/data/Database_Column_Description_waterbilling.csv'
feat_descript = pd.read_csv(csvpath, header=0)
# cols = np.array(feat_descript['Column Header'])  # array of feature names
cols = ['restype', 'edate', 'eyr', 'bill_length', 'bill_tot', 'pen']

# connect/create a databse
conn = sqlite3.connect('./data/waterbilldata_clean_V2.db')

# Create a cursor
c = conn.cursor()
# Run SQL Query
# c.execute("SELECT " + ','.join(cols) + "\
#          FROM wudata")
c.execute("SELECT " + ','.join(cols) + "\
            FROM familywaterbills\
            WHERE(restype='SF') and \
            (pen > 0)")

dbdata = c.fetchall()
conn.close()

# store queried data into dataframe
df_bill = pd.DataFrame(dbdata, columns=cols)

#%% Get subset of data
cols = ['restype', 'edate', 'eyr', 'bill_length', 'billtot', 'pen']
df_subset = df_bill[cols]
df_subset = df_subset[df_subset['pen'].notna() & (df_subset['pen'] != '')]
df_pen = df_subset.groupby('eyr')['pen'].sum()
df_pen