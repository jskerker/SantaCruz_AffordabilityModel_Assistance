#%% import packages
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

#%% define functions

def setup_climate_sims(real_All, dT_All, dP_All, dCV_All, demand_All):
    # get combinations of inputs
    combinations = list(itertools.product(real_All, dT_All, dP_All, dCV_All, demand_All))

    print('all scenario combinations: {}'.format(combinations))

    return combinations


# Purpose: post-process the results dataframe from Pywr
# Inputs:
#   df - dataframe from Pywr model instance
# Outputs:
#   df_processed - processed and cleaned up df
def post_process_results(df):
    # Take out the first empty row of the dataframe and rename the index
    df.columns = df.columns.get_level_values(0).tolist()
    df.index.name = 'Date'
    df.index = df.index.to_timestamp()
    # Sort the column by alphabetic order, and save the dataframe into a.csv file
    df_processed = df.reindex(sorted(df.columns), axis=1)
    return df_processed


def sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add=''):
    # setup parameters for climate combinations
    # get climate combinations
    scenario = setup_climate_sims(real_All, dT_All, dP_All, dCV_All, demand_All)
    # print(type(scenario))
    num_sims = len(scenario)

    # save climate scenario combinations
    headers = ['real', 'dT', 'dP', 'dCV', 'demand']
    # Save the list to a CSV file
    # with open(filepath + 'test_random_combinations_03Sept_NA.csv', 'w', newline='') as file:
    with open(filepath + 'climate_scenarios_{}_dP={}.csv'.format(num_sims, dP_All[0]), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(scenario)

    # set up parameters for versions
    version_parent = 'SCWSM-Option_Analysis'
    version = 'SCWSM-SimOpt_Test'
    options = [None]

    # run one simulation at a time (I think I want to parallelize this)
    start_time = time.time()
    print('num sims: {}'.format(num_sims))
    for i in range(num_sims):
        print('simulation: {}'.format(str(i + 1)))
        print(scenario[i])
        # create an instance of the model
        modelSetup = simSetup(scenario[i][0], scenario[i][1], scenario[i][2], scenario[i][3], options, filepath_SA,
                              scenario[i][4],
                              decision_vars)
        model = modelSetup.m  # convert from simSetup class to pywr model object

        # run the model
        model.run()

        # post-processing
        # results dataframe
        df_results = post_process_results(model.to_dataframe())
        # cashflow df
        df_cashflow = model.parameters['cashflow_model'].df_cashflow
        # add total demands by tier to df_cashflow
        df_cashflow['demand_t1'] = model.parameters['previous_time_step_demand'].arr_demand_by_tier[:, 0]
        df_cashflow['demand_t2'] = model.parameters['previous_time_step_demand'].arr_demand_by_tier[:, 1]
        df_cashflow['demand_t3'] = model.parameters['previous_time_step_demand'].arr_demand_by_tier[:, 2]

        # df time tracker
        df_time_tracker = model.parameters['cashflow_model'].df_time_tracker

        # save results
        # dataframes to save- df_cashflow, df_rates, df_results,
        dataframes = [df_results, df_cashflow, df_time_tracker]  # , df_sample_low, df_sample_high df_sample_random,
        filenames = ['df_results_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, scenario[i][2], scenario[i][1],
                                                                            scenario[i][3], scenario[i][0],
                                                                            scenario[i][4]),
                     'df_cashflow_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, scenario[i][2], scenario[i][1],
                                                                             scenario[i][3], scenario[i][0],
                                                                             scenario[i][4]),
                     'df_time_tracker_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, scenario[i][2],
                                                                                 scenario[i][1], scenario[i][3],
                                                                                 scenario[i][0], scenario[i][4])]

        # Iterate and save each DataFrame as a CSV
        for df, filename in zip(dataframes, filenames):
            df.to_csv(filepath + filename, index=True)

        # save array of all HH data as .npy file
        arr = model.parameters['santa_cruz_demand_MGD'].arr_hh_data
        filename = 'arr_hh_data_{}P{}T{}_dCV{}_real{}_demand{}.npy'.format(name_add, scenario[i][2], scenario[i][1],
                                                                           scenario[i][3],
                                                                           scenario[i][0], scenario[i][4])
        np.save(filepath + filename, arr)

        # save df of HH assisted bill data
        df = pd.concat(model.parameters['assisted_bills'].list_bill_assist_data, ignore_index=True)
        filename = 'df_assisted_bill_{}P{}T{}_dCV{}_real{}_demand{}.parquet'.format(name_add, scenario[i][2],
                                                                                    scenario[i][1], scenario[i][3],
                                                                                    scenario[i][0], scenario[i][4])
        df.to_parquet(filepath + filename, compression='gzip')

        # get df of households (rows) by years with values for number of months getting assistance
        df['Year'] = df['Date'].dt.year
        df_grouped = df.groupby(['account', 'Year'])['does_acct_get_assistance?'].sum().reset_index()
        df_result = df_grouped.pivot(index="account", columns="Year", values="does_acct_get_assistance?").fillna(0)
        df_result.to_csv(filepath + 'df_hh_unafford_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, scenario[i][2],
                                                                                               scenario[i][1],
                                                                                               scenario[i][3],
                                                                                               scenario[i][0],
                                                                                               scenario[i][4]))

        # merge dataframes with annual count of households getting assistance and monthly assistance levels
        df_monthly_assistance = model.parameters['assisted_bills'].df_monthly_assistance
        # print('df monthly assistance: \n', df_monthly_assistance.dtypes)
        df_annual_count_unafford_hhs = model.parameters['planning_afford'].df_count_unafford_hhs
        # print('df annual count unafford hhs: \n', df_annual_count_unafford_hhs.dtypes)
        df_merge = pd.merge(df_monthly_assistance, df_annual_count_unafford_hhs, left_on='Date', right_on='Date',
                            how='left')
        filename = 'df_monthly_assistance_{}P{}T{}_dCV{}_real{}_demand{}.csv'.format(name_add, scenario[i][2],
                                                                                     scenario[i][1], scenario[i][3],
                                                                                     scenario[i][0], scenario[i][4])
        df_merge.to_csv(filepath + filename, index=True)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Model ran in {elapsed_time} seconds')
    return model

#%% Run model- BASELINE sims
# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_IE_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937] #
dT_All = [0, 1] # 1
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']
name_add = 'Baseline_IE_'

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_Baseline.json'
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# no infrastructure
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937] #
name_add = 'Baseline_NoInf_'
decision_vars = [1.0, 0.4, 0.5, 0.3, 0.1, 0.2]
dT_All = [0] # 1
model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
name_add = 'Baseline_'
decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- DEMANDS HIGH
name_add = 'Demands_High_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_Demands_High.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- DEMANDS LOW
name_add = 'Demands_Low_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_Demands_Low.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)


# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- DESAL TIME FAST
name_add = 'DesalTime_Fast_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_DesalTime_Fast.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- DESAL TIME SLOW
name_add = 'DesalTime_Slow_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_DesalTime_Slow.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- INF COSTS HIGH
name_add = 'InfCosts_High_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_InfCosts_High.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- INF COSTS LOW
name_add = 'InfCosts_Low_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_InfCosts_Low.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515] #3574, 4211, 4373, 4937] #
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

# COME BACK TO RUN THIS
decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937] #
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- INTEREST RATE HIGH
name_add = 'InterestRate_High_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_InterestRate_High.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- INTEREST RATE LOW
name_add = 'InterestRate_Low_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_InterestRate_Low.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987] #2770, 3449, 3515, 3574, 4211, 4373, 4937] #
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

# COME BACK TO RUN THIS
decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)
# AND THIS
# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- COST OF SERVICE HIGH
name_add = 'CoS_High_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_CoS_High.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1270, 1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937]
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

#%% Run model- COST OF SERVICE LOW
name_add = 'CoS_Low_'
filepath_SA = '../model_assumptions_and_scenarios/sensitivity_analysis/SA_CoS_Low.json'

# moderate, cool
filepath = '/Volumes/OneTouch/CAPs_Results/Results_SA_Oct2025/'
real_All = [1956, 1987, 2770, 3449, 3515, 3574, 4211, 4373, 4937] #
dT_All = [0, 1]
dP_All = [100]
dCV_All = [1.0]
demand_All = ['Baseline']

decision_vars = [0.654, 0.4, 0.5, 0.3, 0.1, 0.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)

# dry, hot
dT_All = [4, 5]
dP_All = [80, 90]
dCV_All = [1.2]
#model = sim_model_run(decision_vars, filepath, real_All, dT_All, dP_All, dCV_All, demand_All, filepath_SA, name_add)
