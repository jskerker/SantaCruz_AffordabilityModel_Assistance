
import pandas as pd
import os

print(os.getcwd()) # this filepath should be the scripts folder-- if it's not, will need to adjust filepaths
# change this based on your initial path

# Read the file containing the model/system assumptions/parameters that are
# described using a single number (e.g., pipeline capacities, water rights, ...)
system_parameters = pd.read_csv(
    '../model_assumptions_and_scenarios/used_assumptions_CSTE.csv',
    index_col='Assumption')
    
version = system_parameters.columns[0]


# Read the file containing the model/system assumptions/scenarios that are 
# described using monthly profiles (i.e., monthly distribution of the urban 
# and coastal farmer demand, monthly flow rate from the groundwater wells, ...)
system_profiles = pd.read_csv(
    '../model_assumptions_and_scenarios/used_assumptions_PROFILES.csv', # init_path +
    index_col='Assumption')

# Read the file containing the monthly thresholds used to specify the water month type.
# The thresholds are compared to the cumulative sum throughout the water year (starting in October)
# of the San Lorenzo streamflow at Big Trees.
water_month_types_thresholds = pd.read_csv(
    '../model_assumptions_and_scenarios/Hydrological_Condition_Types.csv',
    index_col='Month')