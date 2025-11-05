# Import Python libraries
import sys
import os
import time
import json
import numpy as np
import pandas as pd
import calendar, datetime
import csv
import multiprocessing
#from pywr.core import Model
#from pywr.parameters import Parameter
#from pywr.parameters import load_parameter
#import matplotlib.pyplot as plt
#import runpy

#from mpi4py import MPI

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Import the selected model run assumptions
import scwsm_model_assumptions as scwsm


class householdDemand:

    HHdata = None
    DCCcoef = None

    @classmethod
    def load_csv_hhdata(cls, csv_file_path1):
        #if cls.HHdata is None:
        if cls.HHdata is None:
            cls.HHdata = pd.read_csv(csv_file_path1) # cls.HHdata
        return cls.HHdata 
    
    @classmethod
    def load_csv_dcc_coef(cls, csv_file_path2):
        if cls.DCCcoef is None:
            df = pd.read_csv(csv_file_path2) 
            df.columns = ['key', 'value']
            cls.DCCcoef = df.set_index('key').to_dict(orient='index')
            for key in cls.DCCcoef:
                cls.DCCcoef[key] = float(cls.DCCcoef[key]['value'])
        return cls.DCCcoef    
    

    def __init__(self, margPrices, fixedFees, month, year, curtail=0, tempC=15, precipMM=0, AET=300, rnd_income_group=1, factor=1):

        # import data from json file
        file_name = "../model_assumptions_and_scenarios/cashflow_rate_assumptions.json"
        with open(file_name) as f:
            self.params = json.load(f)  # json parser, could look at numpy and pandas parsers
        for key in self.params:
            setattr(self, key, self.params[key])

        if self.HHdata is not None: #  or HHdata.empty
            self.taxValue = np.array(self.HHdata['tax_value'])
            self.mainArea = np.array(self.HHdata['Main_Area'])
            self.pool = np.array(self.HHdata['Pool2'])
            self.bathrooms = np.array(self.HHdata['Bathrooms_F_H2'])

            # get household residual values
            self.resid_dbc = np.array(self.HHdata['mean_residuals_real']) # 'mean_residuals_log'

            # number of accounts in dataset
            self.num_accts = len(self.HHdata)

            # random income group and column
            self.rnd_income_group = rnd_income_group
            self.col_name_income = 'map_inc_' + str(self.rnd_income_group)

            # add income class to dataset
            col_demand = 'income_class'
            if col_demand not in self.HHdata.columns:
                self.calc_income_class()
            
        else:
            print('hh data is none')


        # climate data
        self.tempC = tempC
        self.precipMM = precipMM
        self.AET = AET

        # sensitivity analysis factor
        self.factor = factor

        # number of days in month/year
        _, self.num_days = calendar.monthrange(year, month)

        # curtailment policy
        self.curtail = curtail

        # set fixed fees by pipe size
        self.fixedFees = fixedFees
        self.calcFixedFees()

        # number of tiers
        self.num_tiers = len(margPrices)
        self.margPrices = margPrices
        tier_cutoffs_array = margPrices['cutoff'].values
        self.tier_cutoffs = np.insert(tier_cutoffs_array, 0, 0)
        self.tier_diff = np.diff(self.tier_cutoffs)

        # get statistics for AR and bills-- hardcoded 5th, 50th, and 95th percentiles for now
        self.prct_low = 0.05
        self.prct_med = 0.5
        self.prct_high = 0.95
        
        # create for loop for column names for totalBills and AR for all income classes and quantiles
        self.income_classes = 16
        prctiles = [self.prct_low, self.prct_med, self.prct_high]
        col_names = []
        col_names_bill = []
        col_names_AR = []
        for ic in np.arange(1, self.income_classes+1):
            for prct in prctiles:
                
                col_name = 'demand_IC{}_Prct{}'.format(ic, prct)
                col_names.append(col_name)
                
                col_name_bill = 'Bill_IC{}_Prct{}'.format(ic, prct)
                col_names_bill.append(col_name_bill)
        
                col_name_AR = 'AR_IC{}_Prct{}'.format(ic, prct)
                col_names_AR.append(col_name_AR)

        self.col_names = col_names + col_names_bill + col_names_AR

        
    # this function computes the household demands using the DCC model coefficients in a vectorized form
    def calcHHdemand_vectorized(self):

        # add pandas dataframe columns for household demands and marginal prices
        self.HHdata['demand'] = 0.0
        self.HHdata['marg_price'] = 0.0
        self.HHdata['tier'] = 0
        self.HHdata['demand_sum'] = 0.0

        # 1. create array for length of dataframe
        Q = np.zeros((len(self.HHdata), self.num_tiers))
             
        # 2. for each tier, calculate the household water demands based on different marginal prices
        for tier in range(0, self.num_tiers):
             mPrice = self.margPrices.price[self.num_tiers-1-tier]

            # compute log of demands
             logQ = (self.DCCcoef['beta0'] + self.DCCcoef['betaPAl']*np.log(mPrice) + self.DCCcoef['betaTax']*np.log(self.taxValue) + self.DCCcoef['betaMA']*self.mainArea
                 + self.DCCcoef['betaBath']*self.bathrooms + self.DCCcoef['betaBathSq']*(self.bathrooms**2) + self.DCCcoef['betaPool']*self.pool
                 + self.DCCcoef['betaCurtail']*self.curtail + self.DCCcoef['betaAET']*self.AET + self.DCCcoef['betaPrecip']*self.precipMM + self.DCCcoef['betaTemp']*self.tempC
                     )

             Q[:,tier] = np.exp(logQ) + self.resid_dbc

        # 3. set up conditions and values
        lst_conditions = []
        lst_values = []
        lst_tiers = []
        lst_margPrices = []

        # loop through tiers to check tier for all households
        for tier in range(self.num_tiers, 0, -1): # loop from highest to lowest
            mPrice = self.margPrices.price[tier-1]
            lb = self.tier_cutoffs[tier-1]
            ub = self.tier_cutoffs[tier]

            lst_conditions.append(Q[:,self.num_tiers-tier] >= ub)
            lst_conditions.append(Q[:,self.num_tiers-tier] > lb)
            lst_values.append(np.repeat(ub, self.num_accts)) # len(test.HHdata
            lst_values.append(Q[:,self.num_tiers-tier])
            lst_tiers.append(np.repeat(tier, self.num_accts))
            lst_tiers.append(np.repeat(tier, self.num_accts))
            lst_margPrices.append(np.repeat(self.margPrices.price[tier-1], self.num_accts))
            lst_margPrices.append(np.repeat(self.margPrices.price[tier-1], self.num_accts))

        # 4. use np.select
        result_Q = np.select(lst_conditions, lst_values, default=0)
        result_tier = np.select(lst_conditions, lst_tiers, default=0)
        result_margPrices = np.select(lst_conditions, lst_margPrices, default=0)

        # 5. add to HHdata dataframe
        self.HHdata.loc[:,'demand'] = result_Q
        self.HHdata['demand'] = self.HHdata['demand'] * self.factor  # SA
        self.HHdata.loc[:,'marg_price'] = result_margPrices
        self.HHdata.loc[:,'tier'] = result_tier
        self.HHdata.loc[:,'demand_sum'] += result_Q

    # this function takes in the household demands and computes the sum of monthly demands, converted to MG from CCF
    def calcQ(self):
        #print('sum total Q in MGD')
        col_demand = 'demand'
        if col_demand not in self.HHdata.columns:
        #self.calcHHdemand()
        #self.calcHHdemand_parallel()
            self.calcHHdemand_vectorized()
        ccf_to_mg = 748.052/1e6
        Q_mgd = ccf_to_mg * self.HHdata['demand'].sum() / self.num_days
        return Q_mgd

    # function computes the fixed fees for water costs
    # fixedFees should be a pandas dataframe with two columns: (1) pipe_size and (2) the fixed fee
    def calcFixedFees(self):
        # Merge the DataFrames on the 'pipe_size' column
        self.HHdata = pd.merge(self.HHdata, self.fixedFees, on='pipe_size', how='left')


    # function computes the variable water bill costs
    def calcVarCosts(self):
        #print('calculate variable costs')
        col_demand = 'demand'
        if col_demand not in self.HHdata.columns:
            self.calcHHdemand()
        # Define conditions and choices for np.select
        conditions = [
            self.HHdata['tier'] == 1,
            self.HHdata['tier'] == 2,
            self.HHdata['tier'] == 3
        ]

        # switched this to margPrices2
        choices = [
            self.HHdata['demand'] * self.margPrices.loc[0, 'price'],
            self.margPrices.loc[0, 'cutoff'] * self.margPrices.loc[0, 'price'] + (
                        self.HHdata['demand'] - self.margPrices.loc[0, 'cutoff']) * self.margPrices.loc[1, 'price'],
            self.margPrices.loc[0, 'cutoff'] * self.margPrices.loc[0, 'price'] + (
                        self.margPrices.loc[1, 'cutoff'] - self.margPrices.loc[0, 'cutoff']) * self.margPrices.loc[1, 'price'] \
            + (self.HHdata['demand'] - self.margPrices.loc[1, 'cutoff']) * self.margPrices.loc[2, 'price']
        ]

        # Apply the conditions and choices
        self.HHdata['vol_cost'] = np.select(conditions, choices, default=np.nan)
        self.HHdata['vol_cost'] = self.HHdata['vol_cost'].fillna(0)

    # function calculates the total water bill costs
    def calc_water_bill(self):
        #print('calculate total water bill costs')
        col_fixed = 'fixed_rts_fees'
        col_var = 'vol_cost'
        if col_fixed not in self.HHdata.columns:
            self.calcFixedFees()
        if col_var not in self.HHdata.columns:
            self.calcVarCosts()
        self.HHdata['totalWaterCosts'] = self.HHdata['fixed_rts_fees'] + self.HHdata['vol_cost']

    # function to return household water bills for all accounts
    def getWaterBills(self):
        col_bill = 'totalWaterCosts'
        if col_bill not in self.HHdata.columns:
            self.calc_water_bill()
        return self.HHdata['totalWaterCosts'].to_numpy()

    # function calculates the total water bill costs with assistance adjustment
    def calc_water_bill_assist(self):
        #print('calculate total water bill costs')
        col_fixed = 'fixed_rts_fees'
        col_var = 'vol_cost'
        if col_fixed not in self.HHdata.columns:
            self.calcFixedFees()
        if col_var not in self.HHdata.columns:
            self.calcVarCosts()
        account_condition = self.HHdata['account'].isin(dataframe_x['account'])
        self.HHdata['totalWaterCostsAssist'] = np.where(
            account_condition,
            self.HHdata['fixed_rts_fees'] + self.HHdata['vol_cost'] * self.AR_Assist,
            self.HHdata['fixed_rts_fees'] + self.HHdata['vol_cost'])
        self.HHdata['bill_savings'] = self.HHdata['vol_cost'] - (self.HHdata['vol_cost'] * self.AR_Assist)

    # function calculates and returns the affordability ratio for all households in numpy array
    def calcAR(self):
        #print('calculate affordability ratios')
        col_bill = 'totalWaterCosts'
        if col_bill not in self.HHdata.columns:
            self.calc_water_bill()
        self.HHdata['mapped_income'] = self.HHdata[self.col_name_income] # added on 3/5 by jbs
        self.HHdata['AR'] = self.HHdata['totalWaterCosts']/(self.HHdata[self.col_name_income]/12)*100
        return self.HHdata['AR'].to_numpy()


    # function that takes the df columns for demand, bills, and AR and returns as a numpy array
    def get_arr_hh_data(self):
        col_AR = 'AR'
        # check that we have calculated ARs
        if col_AR not in self.HHdata.columns:
            self.calcAR()
        col_names = ['demand', 'totalWaterCosts', 'AR']
        hh_data = self.HHdata[col_names]
        return hh_data.to_numpy()

    # function that takes in a set of household accounts/dataframe indices, and outputs a df of the
    # demand and water costs for those households
    def get_sample_hh_data(self, hhs_index):
        col_AR = 'AR'
        if col_AR not in self.HHdata.columns:
            self.calcAR()
        col_names = ['demand', 'totalWaterCosts']
        hh_data = self.HHdata[col_names].loc[hhs_index]
        return hh_data

    # function that takes in a set of household accounts/dataframe indices, and outputs an array of the
    # ARs for those households
    def get_sample_hh_data_ARs(self, hhs_index):
        col_AR = 'AR'
        if col_AR not in self.HHdata.columns:
            self.calcAR()
        hh_data = self.HHdata[col_AR].loc[hhs_index].to_numpy()
        return hh_data

    # function to put together one row of data for stats dataframe
    def get_water_stats_row(self):
        # calculate water bills or AR if they haven't been calculated
        col_bill = 'totalWaterCosts'
        col_AR = 'AR'
        if col_AR not in self.HHdata.columns:
            self.calcAR()
        AR = self.HHdata[col_AR].iloc[0]
        
        quantile_demand = self.HHdata.groupby('income_class')['demand'].quantile([self.prct_low, self.prct_med, self.prct_high])
        quantile_bill = self.HHdata.groupby('income_class')['totalWaterCosts'].quantile([self.prct_low, self.prct_med, self.prct_high])
        quantile_AR = self.HHdata.groupby('income_class')['AR'].quantile([self.prct_low, self.prct_med, self.prct_high])

        arr_combined = np.concatenate((quantile_demand.values, quantile_bill.values, quantile_AR.values))
        arr_combined = arr_combined.reshape(1, -1)

        new_row = pd.DataFrame(data=arr_combined, columns=self.col_names)
        return new_row

    # function just returns the dataframe of data with AR included
    def get_hh_data_assist(self):

        # check that water use and AR data is already computed
        col_AR = 'AR'

        if col_AR not in self.HHdata.columns:
            self.calcAR()

        self.hh_bill_data = self.HHdata

        return self.hh_bill_data

    # function to get household level water demands
    def get_hh_data(self):
        col_AR = 'AR'

        if col_AR not in self.HHdata.columns:
            self.calcAR()

        ## get random households
        # Group the DataFrame by 'income_class' column and sample a random index or account for each group
        hh_ind_by_class = self.HHdata

        cols_to_include = ['account', 'mapped_income', 'income_class', 'demand',
                           'fixed_rts_fees', 'vol_cost', 'totalWaterCosts', 'AR', 'tier', 'marg_price']

        # new dataframe for random data for specific income classes
        self.df_hh_data = hh_ind_by_class[cols_to_include]

        # get water use by tier
        self.calc_tiered_water_use_hh()

        self.df_hh_data['unafford'] = (self.df_hh_data['AR'] > self.AR_thresh).astype(int)

        return self.df_hh_data

    # function calculates the water use in each tier for every account for get_hh_data
    def calc_tiered_water_use_hh(self):

        demand_remaining = self.df_hh_data.loc[:, 'demand']
        self.df_hh_data = self.df_hh_data.copy()
        for i in range(self.num_tiers):
            col_name = 'tier_' + str(i + 1)
            self.df_hh_data.loc[:, col_name] = np.maximum(np.minimum(demand_remaining, self.tier_diff[i]), 0)
            demand_remaining = demand_remaining - self.tier_diff[i]

    
    # function to get representative household water demands-- for now 1 household/account for a few income groups
    def get_representative_hh_data(self):
        
        # check that water use and AR data is already computed
        col_AR = 'AR'

        if col_AR not in self.HHdata.columns:
            self.calcAR()

        ## get random households
        # Group the DataFrame by 'income_class' column and sample a random index or account for each group
        random_ind_by_class = self.HHdata.groupby('income_class').apply(lambda x: x.sample(n=1))

        # extract random households and certain columns
        cols_to_include = ['account', self.col_name_income, 'income_class', 'demand',
                   'fixed_rts_fees', 'vol_cost', 'totalWaterCosts', 'AR', 'tier', 'marg_price']
        
        # new dataframe for random data for specific income classes
        self.df_random_data = random_ind_by_class[cols_to_include]
        
        # get water use by tier
        self.df_random_data = self.calc_tiered_water_use()
        
        return self.df_random_data
    
    # function returns the number of accounts in the household dataset
    def numAccounts(self):
        return len(self.HHdata)

    # function returns an array with the sum of monthly demands in ccf for each tier
    def sum_demand_by_tier(self):
        df = self.HHdata['demand']
        allocated_demand = self.allocate_demand(df)
        
        # Sum the allocations for each tier
        tier_sums = pd.Series(allocated_demand.sum(axis=0), index=[f'tier{i+1}' for i in range(self.num_tiers)])
        return tier_sums.values
    
    # function is a helper function that loops through each tier and allocates the demands
    def allocate_demand(self, demands):
        allocated_demand = np.zeros((demands.size, self.num_tiers)) # create empty array for allocated demands- rows are each HH, columns are the tiers

        # Loop through each tier and allocate the demand
        for i in range(self.num_tiers):
            if i == 0:
                allocated_demand[:, i] = np.minimum(demands, self.tier_cutoffs[i+1])
            else:
                previous_cutoff = self.tier_cutoffs[i]
                current_cutoff = self.tier_cutoffs[i+1]
                allocated_demand[:, i] = np.minimum(np.maximum(demands - previous_cutoff, 0), current_cutoff - previous_cutoff)

        return allocated_demand

    
    # function calculates the income class for the household data
    def calc_income_class(self):
        bins = [0, 10000, 14999, 19999, 24999, 29999, 34999, 39999, 44999, 49999, 59999, 74999, 99999, 
                        124999, 149999, 199999, 1000000]
        print('income class column: ', self.col_name_income)

        self.HHdata['income_class'] = np.digitize(self.HHdata[self.col_name_income], bins, right=True)
        
    # function calculates the water use in each tier for every account
    def calc_tiered_water_use(self):

        demand_remaining = self.df_random_data.loc[:, 'demand']
        self.df_random_data = self.df_random_data.copy()
        for i in range(self.num_tiers):
            col_name = 'tier_' + str(i+1)
            self.df_random_data.loc[:, col_name] = np.maximum(np.minimum(demand_remaining, self.tier_diff[i]), 0)
            demand_remaining = demand_remaining - self.tier_diff[i]
        
        return self.df_random_data
