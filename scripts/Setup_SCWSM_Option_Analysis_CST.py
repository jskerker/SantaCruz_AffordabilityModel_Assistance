# Import Python libraries
import os
import json
import numpy as np
import pandas as pd
# import calendar, datetime
from pywr.core import Model

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



class simSetup:

    def __init__(self, real, dT, dP, dCV, options, file_SA, demand='', decision_vars=[0.5, 0.2, 0.3, 0.4, 0.5, 0.6]):

        we_need_to_generate_jsons = True

        # set up file saving names
        if demand == '':
            version = 'SCWSM-Option_Analysis'
        else:
            version = 'SCWSM-Demand_' + demand
        version_parent = 'SCWSM-Option_Analysis'

        # Path for json files describing the system
        path_model = '../models/{}/{}/json_models/'.format(version_parent, version)

        # Path results
        path_results = '../results/{}/{}/'.format(version_parent, version)

        # check if a results and model folders exist for this version of the model
        if not os.path.exists(path_results):
            # create the path
            os.makedirs(path_results)
            open(path_results + '.gitkeep', 'a').close()

        if not os.path.exists(path_model):
            # create the path
            os.makedirs(path_model)
            # create a .gitkeep empty file to enable pushing the folder through git even if ignoring the
            # created .csv files
            open(path_model + '.gitkeep', 'a').close()

        # import model assumptions and scenarios
        # file not included in Github repo
        model_assumptions_CSTE = pd.read_csv(
            '../model_assumptions_and_scenarios/model_assumptions_CSTE.csv',
            index_col='Assumption', usecols=['Assumption', version])
        
        model_assumptions_CSTE.to_csv(
            '../model_assumptions_and_scenarios/used_assumptions_CSTE.csv')

        # file not included in Github repo
        model_assumptions_PROFILES = pd.read_excel(
            '../model_assumptions_and_scenarios/model_assumptions_PROFILES.xlsx',
            sheet_name=version, index_col='Assumption')
        model_assumptions_PROFILES.to_csv(
            '../model_assumptions_and_scenarios/used_assumptions_PROFILES.csv') # init_path + '/model_assumptions...'


        # Create the jsons file required for the chosen scenarios
        if we_need_to_generate_jsons:
            # made this a function instead of using the exec() function
            self.buildModel(version, version_parent, real, dT, dP, dCV, demand, options, decision_vars, file_SA)

        # import parameter classes
        from scwsm_demands import HOUSEHOLD_DEMAND_DYNAMIC
        HOUSEHOLD_DEMAND_DYNAMIC.register()
        from scwsm_demands import WATER_RATE_STRUCTURE
        WATER_RATE_STRUCTURE.register()
        from scwsm_demands import CHECK_PLANNING_INF
        CHECK_PLANNING_INF.register()
        from scwsm_demands import GET_PREVIOUS_DEMAND
        GET_PREVIOUS_DEMAND.register()
        from scwsm_demands import TIME_TRACKER
        TIME_TRACKER.register()
        from scwsm_demands import CASHFLOW_MODEL
        CASHFLOW_MODEL.register()
        from scwsm_demands import CHECK_HOUSE_AFFORD
        CHECK_HOUSE_AFFORD.register()
        from scwsm_demands import CALC_ASSIST_BILL
        CALC_ASSIST_BILL.register()

        # IMPORT PARAMETERS THAT PRIMARILY DESCRIBE SYSTEM OPERATIONS AND/OR CONSTRAINTS
        # parameters not included in Github repo
        from scwsm_operations_and_constraints import Max_Flow_Below_LL
        # An updated version of the parameter below is now defined in the alternative
        # supply operations module (see further below)
        from scwsm_operations_and_constraints import hydraulic_constraint
        Max_Flow_Below_LL.register()
        hydraulic_constraint.register()

        #print('import water rights params')
        # IMPORT PARAMETERS THAT PRIMARILY DESCRIBE WATER RIGHTS
        # parameters not included in Github repo
        from scwsm_water_rights import Felton_to_LL_Annual_License
        from scwsm_water_rights import WATER_RIGHT_NEWELL_TO_GHWTP
        from scwsm_water_rights import WATER_RIGHT_NEWELL_DIV_TO_LL
        from scwsm_water_rights import PRECIP_WATER_IN_LL
        from scwsm_water_rights import FELTON_WATER_IN_LL
        from scwsm_water_rights import NEWELL_WATER_IN_LL
        from scwsm_water_rights import USEABLE_PRCP_TO_GHWTP
        from scwsm_water_rights import WATER_MONTH_TPYE
        from scwsm_water_rights import SWITCH_MCASR_INJECTION
        from scwsm_water_rights import SWITCH_TRANSFERS
        Felton_to_LL_Annual_License.register()
        WATER_RIGHT_NEWELL_TO_GHWTP.register()
        WATER_RIGHT_NEWELL_DIV_TO_LL.register()
        PRECIP_WATER_IN_LL.register()
        FELTON_WATER_IN_LL.register()
        NEWELL_WATER_IN_LL.register()
        USEABLE_PRCP_TO_GHWTP.register()
        WATER_MONTH_TPYE.register()
        SWITCH_MCASR_INJECTION.register()
        SWITCH_TRANSFERS.register()

        # IMPORT PARAMETERS THAT ARE DESIGNED FOR THE ASSESSMENT OF ALTERNATIVE SUPPLY
        # OPTIONS
        # parameters not included in Github repo
        from scwsm_alternative_supply_option_operations import FELTON_DIV_TO_LL
        from scwsm_alternative_supply_option_operations import DESALINATION_PLANT_YIELD
        from scwsm_alternative_supply_option_operations import DIRECT_POTABLE_REUSE_PLANT_YIELD
        from scwsm_alternative_supply_option_operations import DEMAND_AFTER_RATIONING
        from scwsm_alternative_supply_option_operations import SUPPLY_GAP
        from scwsm_alternative_supply_option_operations import MCGWB_SWITCH
        from scwsm_alternative_supply_option_operations import Soquel_SWITCH
        from scwsm_alternative_supply_option_operations import UPDATE_DESALT_V2
        from scwsm_alternative_supply_option_operations import UPDATE_DESALT_CAPACITY
        from scwsm_alternative_supply_option_operations import TRANSFER_YIELD
        from scwsm_alternative_supply_option_operations import UPDATE_MCASR
        from scwsm_alternative_supply_option_operations import UPDATE_SMASR
        from scwsm_alternative_supply_option_operations import UPDATE_TRANSFER_SOQUEL
        from scwsm_alternative_supply_option_operations import UPDATE_TRANSFER_SCOTTS_VALLEY
        from scwsm_alternative_supply_option_operations import UPDATE_DPR
        FELTON_DIV_TO_LL.register()
        DESALINATION_PLANT_YIELD.register()
        DIRECT_POTABLE_REUSE_PLANT_YIELD.register()
        DEMAND_AFTER_RATIONING.register()
        SUPPLY_GAP.register()
        MCGWB_SWITCH.register()
        Soquel_SWITCH.register()
        UPDATE_DESALT_V2.register()
        UPDATE_DESALT_CAPACITY.register()
        TRANSFER_YIELD.register()
        UPDATE_MCASR.register()
        UPDATE_SMASR.register()
        UPDATE_TRANSFER_SOQUEL.register()
        UPDATE_TRANSFER_SCOTTS_VALLEY.register()
        UPDATE_DPR.register()

        # Define the decision variables
        rof_thresh = f"{decision_vars[0]:.2f}"
        # inf order
        arr = np.array(decision_vars[1:])
        rank_order = np.argsort(np.argsort(arr)) + 1

        # Create the scenario to be run by the model
        model_mpi = []
        model_mpi.append('SCWSM_P{}T{}_R{}_dCV={}_D{}_rof{}_soq{}_sv{}_mc{}_des{}.json'.format(dP, dT, real, dCV, demand, rof_thresh,
                                                                                               rank_order[0], rank_order[1], rank_order[2], rank_order[3]))
        self.m = Model.load(path_model + model_mpi[0])


    def execute_code(self, code):
        exec(code)

    def buildModel(self, version, version_parent, real, dT, dP, dCV, demand, options, decision_vars, file_SA):

        # Import the selected model run assumptions
        # import used system parameters
        # file predecessor not included in Github repo
        system_parameters = pd.read_csv(
            '../model_assumptions_and_scenarios/used_assumptions_CSTE.csv',
            index_col='Assumption')

        # Read the file containing the model/system assumptions/scenarios that are
        # described using monthly profiles (i.e., monthly distribution of the urban
        # and coastal farmer demand, monthly flow rate from the groundwater wells, ...)
        # file not included in Github repo
        system_profiles = pd.read_csv(
            '../model_assumptions_and_scenarios/used_assumptions_PROFILES.csv',  # init_path +
            index_col='Assumption')

        # Path to the csv file containing the streamflow input
        # files on Zenodo
        flow_path = '../../../../../Santa_Cruz_WRM_updated/data/input_climate_stress_test/FLOW/' \
                    'FLOW_P{}T{}_R{}_dCV={}.csv'


        # Path to the csv file containing the weather input
        # files on Zenodo
        weather_path = '../../../../../Santa_Cruz_WRM_updated/data/input_climate_stress_test/WEATHER/' \
                       'weather_dT={}_dP={}_R{}_dCV={}.csv'

        # monthly climate files- in zip file on Github
        monthly_path = '../../../../../Santa_Cruz_WRM_updated/data/climate_monthly/' \
                       'climate_monthly_dT={}_dP={}_R{}_dCV={}.csv'


        list_paramters_requiring_streamflow_input = (
            'flow_bigtrees_naturalized_CFS',
            'flow_bigtrees_CFS',
            'flow_taitside_CFS',
            'flow_newell_creek_CFS',
            'flow_liddell_spring_CFS',
            'flow_laguna_creek_CFS',
            'flow_majors_creek_CFS',
            'First_Flush',
            'DRY_CLASS_Beltz_12'
        )

        list_paramters_requiring_weather_input = (
            'precipitation_loch_lomond_inch',
            'evaporation_loch_lomond_inch',
            'Turbidity_SLR',
            'Turbidity_Tait',
            'Turbidity_NC',
            'Turbidity_MAJORS'
        )
        
        list_parameters_requiring_monthly_input = (
            'precipitation_monthly_mm',
            'evaporation_monthly_mm',
            'temperature_monthly_degC'
        )

        with open('../models/{}/Parent/'
                  'CST_SCWSM_OPTION_ANALYSIS_SA.json'.format(version_parent)) as (
        #          'CST_SCWSM_OPTION_ANALYSISjson'.format(version_parent)) as (
        master_script):
            # Load the parent file
            file_master = json.load(master_script)

            # Set simulation start and end dates
            file_master['timestepper']['start'] = "{}-{}-{}".format(
                int(system_parameters[version]['Simulation Start Year']),
                int(system_parameters[version]['Simulation Start Month']),
                int(system_parameters[version]['Simulation Start Day'])
            )

            file_master['timestepper']['end'] = "{}-{}-{}".format(
                int(system_parameters[version]['Simulation End Year']),
                int(system_parameters[version]['Simulation End Month']),
                int(system_parameters[version]['Simulation End Day'])
            )

            # Streamflow input file
            # ---------------------
            # Assigning the path to the streamflow input
            for parameter in list_paramters_requiring_streamflow_input:
                file_master['parameters'][parameter]['url'] = \
                    flow_path.format(dP, dT, real, dCV)

            # Precipitation and evaporation over the Loch Lomond reservoir
            # ------------------------------------------------------------
            for parameter in list_paramters_requiring_weather_input:
                file_master['parameters'][parameter]['url'] = \
                    weather_path.format(dT, dP, real, dCV)

            # Monthly precip, evap, and temp data
            # ------------------------------------------------------------
            for parameter in list_parameters_requiring_monthly_input:
                file_master['parameters'][parameter]['url'] = \
                    monthly_path.format(dT, dP, real, dCV)

            LL_level_th = pd.read_csv('../results/LL_level_quantiles.csv')

            if 'Tait St WR (SLR withdrawal + well)(MGD)' in system_parameters[version]:
                #print('key found')
                self.tait_st_diversion_max = system_parameters[version][
                    'Tait St WR (SLR withdrawal + well)(MGD)']

            threshold_value = str(system_parameters[version]['LL_threshold_Soquel_switch (fraction)'])
            file_master['parameters']["loch_lomond_level_quantiles"]['values'] = \
                LL_level_th['Level_{}th_MG'.format(threshold_value)].tolist()

            file_master['parameters']['Soquel_to_demand_max_flow']['values'] = \
                system_profiles.loc['Soquel_to_demand_max_flow_MGD'].tolist()

            file_master['parameters']["ghwtp_to_Soquel_max_flow"]['values'] = \
                system_profiles.loc['ghwtp_to_Soquel_max_flow_MGD'].tolist()

            # Turbidity of SLR at Felton diversion
            file_master['parameters']['Turbidity_SLR']['column'] = "Turbidity_SLR"

            # Urban demand
            # ------------

            # Monthly profile for non-residential demands
            #print('santa cruz non-res demand: ', system_profiles.loc['santa_cruz_demand_other_MGD'].tolist())
            #print('santa cruz MF demand: ', system_profiles.loc['santa_cruz_MF_demand_MGD'].tolist())
            file_master['parameters']['santa_cruz_demand_other_MGD']['values'] = \
                system_profiles.loc['santa_cruz_demand_other_MGD'].tolist()

            # Monthly profile for multi-family residential demands
            file_master['parameters']['santa_cruz_MF_demand_MGD']['values'] = \
                system_profiles.loc['santa_cruz_MF_demand_MGD'].tolist()

            # Monthly profile for losses
            file_master['parameters']['santa_cruz_losses_MGD']['values'] = \
                system_profiles.loc['santa_cruz_losses_MGD'].tolist()

            # Daily demand for the San Lorenzo Valley district
            file_master['parameters']['san_lorenzo_valley_district_demand']['value'] = \
                system_parameters[version][
                    'Daily deliveries to San Lorenzo Valley District (MGD)']

            # Coastal farmer demand
            # ---------------------

            # Annual Coastal Farmer Demand
            file_master['parameters']['santa_cruz_farmer_demand_annual_MGD']['value'] = \
                system_parameters[version]['Annual Farmer Demand (MG)']

            # Monthly profile for the Coastal Farmer Demand
            file_master['parameters']['santa_cruz_farmer_demand_profile']['values'] = \
                system_profiles.loc['Farmer Demand monthly distribution (%)'].tolist()

            # Set pipeline, diversion and other system parameters
            # ---------------------------------------------------

            # Laguna diversion capacity
            file_master['parameters']['laguna_div_max_flow']['value'] = \
                system_parameters[version]['Laguna div capacity (MGD)']

            # Majors diversion capacity
            file_master['parameters']['majors_div_max_flow']['value'] = \
                system_parameters[version]['Majors div capacity (MGD)']

            # Liddell diverson capacity
            file_master['parameters']['liddell_div_max_flow']['value'] = \
                system_parameters[version]['Liddell div capacity (MGD)']

            # North Coast pipeline capacity
            file_master['parameters']['north_coast_pipeline_max_flow']['value'] = \
                system_parameters[version]['NorthCoast pipeline capacity (MGD)']

            # Beltz wells capacity (currently set equal to the 'water right')
            file_master['parameters']['beltz_tp_max_capacity']['value'] = \
                system_parameters[version]['Betlz TP max capacity (MGD)']
            file_master['parameters']['beltz_12_tp_max_capacity']['value'] = \
                system_parameters[version]['Betlz 12 TP max capacity (MGD)']

            # Total diversion capacity at Tait' street
            file_master['parameters']['tait_total_max_flow']['value'] = \
                system_parameters[version]['Tait St (total) div capacity (MGD)']

            # Felton buffer (minimum flow required below Felton diversion)
            file_master['parameters']['felton_buffer']['value'] = \
                system_parameters[version]['Felton buffer (MGD)']

            # Diversion capacity from LL reservoir to GHWTP
            file_master['parameters']['max_ll_ghwtp']['value'] = \
                system_parameters[version]['Max div from LL to GHWTP (MGD)']

            # Initial and maximum storage at Loch Lomond
            ll_reservoir_node = [i for i, d in enumerate(file_master['nodes'])
                                 if d.get('name', '') == 'll_reservoir'][0]

            file_master['nodes'][ll_reservoir_node]['initial_volume'] = \
                system_parameters[version]['LL initial storage (MG)']
            file_master['nodes'][ll_reservoir_node]['max_volume'] = \
                system_parameters[version]['LL maximum storage (MG)']

            # Set the profiles (i.e., set of 12 monthly values defining seasonal
            # capacities)
            # -------------------------------------------------------------------

            # Monthly profile for injection of Beltz groundwater wells
            file_master['parameters']['Beltz_8_well_injection_max_MGD']['values'] = \
                system_profiles.loc['beltz_8_well_injection_max_MGD'].tolist()

            file_master['parameters']['Beltz_9_well_injection_max_MGD']['values'] = \
                system_profiles.loc['beltz_9_well_injection_max_MGD'].tolist()

            file_master['parameters']['Beltz_10_well_injection_max_MGD']['values'] = \
                system_profiles.loc['beltz_10_well_injection_max_MGD'].tolist()

            file_master['parameters']['Beltz_12_well_injection_max_MGD']['values'] = \
                system_profiles.loc['beltz_12_well_injection_max_MGD'].tolist()

            file_master['parameters']['New_ASR_1_injection_max_MGD']['values'] = \
                system_profiles.loc['new_ASR_1_injection_max_MGD'].tolist()

            file_master['parameters']['New_ASR_2_injection_max_MGD']['values'] = \
                system_profiles.loc['new_ASR_2_injection_max_MGD'].tolist()


            # Monthly profile for extraction of Beltz groundwater wells
            file_master['parameters']['Beltz_8_well_extraction_max_MGD']['values'] = \
                system_profiles.loc['beltz_8_well_extraction_max_MGD'].tolist()

            file_master['parameters']['Beltz_9_well_extraction_max_MGD']['values'] = \
                system_profiles.loc['beltz_9_well_extraction_max_MGD'].tolist()

            file_master['parameters']['Beltz_10_well_extraction_max_MGD']['values'] = \
                system_profiles.loc['beltz_10_well_extraction_max_MGD'].tolist()

            file_master['parameters']['Beltz_12_well_extraction_max_MGD']['values'] = \
                system_profiles.loc['beltz_12_well_extraction_max_MGD'].tolist()

            file_master['parameters']['New_ASR_1_extraction_max_MGD']['values'] = \
                system_profiles.loc['new_ASR_1_extraction_max_MGD'].tolist()

            file_master['parameters']['New_ASR_2_extraction_max_MGD']['values'] = \
                system_profiles.loc['new_ASR_2_extraction_max_MGD'].tolist()

            # Monthly profile for Tait's well
            file_master['parameters']['tait_well_extraction_max_MGD']['values'] = \
                system_profiles.loc['tait_well_extraction_max_MGD'].tolist()

            # Felton water right cannot be used at the Tait's diversion
            if system_parameters[version]['UseCombinedWRatTait'] == 0:
                file_master['parameters']['tait_div_max_flow']['values'] = \
                    system_profiles.loc['Tait St WR (SLR withdrawal + well)(MGD)'].tolist()

                # Remove the aggregated Felton water right node that constraint the daily diversion
                # from the Felton water right at Tait and Felton divsersions
                felton_wr_node = [i for i, d in enumerate(file_master['nodes'])
                                  if d.get('name', '') == 'felton_water_right'][0]

                del file_master['nodes'][felton_wr_node]

            # Felton water right can be used at the Tait's diversion
            else:
                # Tait's water right (daily extraction from SLR and groundwater wells)
                file_master['parameters']['tait_div_max_flow']['values'] = \
                    system_profiles.loc['Tait and Felton WR combined (MGD)'].tolist()

            # Monthly profile for pumping from GHWTP to Scotts Valley
            file_master['parameters']['ghwtp_to_transfer_Scotts_Valley_max_MGD']['values'] = \
                system_profiles.loc['ghwtp_to_transfer_Scotts_Valley_max_MGD'].tolist()

            # Monthly profile for pumping from Scotts Valley to demand
            file_master['parameters']['Scotts_Valley_to_transfer_demand_max_MGD']['values'] = \
                system_profiles.loc['Scotts_Valley_to_transfer_demand_max_MGD'].tolist()

            # Set the parameters and assumptions related to the Aquifer Storage and
            # Recovery option (ASR) to default values
            # -------------------------------------------------------------------

            # Loop over the groundwater basin (Santa Margarita GWB;  Mid-County GWB)
            for gwb in ('SMGWB', 'MCGWB'):  # changed () to []

                # ASR injection rate loss
                asr_net_injection_node = [i for i, d in enumerate(file_master['nodes'])
                                          if d.get('name', '') == '{}_ASR_net_injection'.format(gwb)][0]
                file_master['nodes'][asr_net_injection_node]['loss_factor'] = \
                    system_parameters[version]['{} ASR injection rate loss (fraction)'.format(gwb)]

            # Set the cost attributes to the Loch Lomond storage levels as a function of of the 'drought reserve'
            # The term 'drought reserve' refers to the Loch Lomond volume from which the Felton Booster pump
            # will no longer be used (i.e., no more transfer from Loch Lomond to the water treatment plant).
            fraction_drought_reserve = \
                system_parameters[version]['LL drought reserve (MG)'] \
                / system_parameters[version]['LL maximum storage (MG)']

            # Create the control cuvees (i.e., fraction of LL storage) above the drought reserve
            control_curve_above_drought_reserve = \
                np.round(np.linspace(1, fraction_drought_reserve, 11), 5)[1:].tolist()
            # Add two levels below the drought reserve. One is just below, and the last one is 10% of filling level
            control_curve_above_drought_reserve.extend([control_curve_above_drought_reserve[-1] - 0.00001, 0.1])

            # Update the 'control_curves' attributes of the 'loch_lomond_water_value' parameters
            file_master['parameters']['loch_lomond_water_value']['control_curves'] = \
                [x for x in control_curve_above_drought_reserve]

            # income mapping to use
            inc = 3
            file_master['parameters']['hh_income_map']['value'] = int(inc)

            # decision variables
            # 1. rof threshold
            rof_thresh = f"{decision_vars[0]:.2f}"
            file_master['parameters']['threshold_rof']['value'] = decision_vars[0]

            # take array of values between 0 and 1 and convert to values from 1-5
            arr = np.array(decision_vars[1:])
            rank_order = np.argsort(np.argsort(arr)) + 1 # get the indices that sort the values in ascending order, then the rank
            print('rank order: ', rank_order)

            # 2. order of Soquel transfer
            file_master['parameters']['order_TRANSFER_SOQUEL']['value'] = int(rank_order[0])

            # 3. order of Scotts Valley transfer
            file_master['parameters']['order_TRANSFER_SCOTTS_VALLEY']['value'] = int(rank_order[1])

            # 4. order of MCASR
            file_master['parameters']['order_MCASR']['value'] = int(rank_order[2])

            # 5. order of Desal
            file_master['parameters']['order_DESALT_4MGD']['value'] = int(rank_order[3])

            # 6. order of DPR`
            file_master['parameters']['order_DPR']['value'] = int(rank_order[4])

            # If there are options
            if options is not None:
                # Set the values below to 1 allows injection and extraction to/from the
                # ASR storage (default value is 0)
                if 'SMASR' in options:
                    file_master['parameters']['is_SMGWB_ASR_included']['value'] = 1

                if 'MCASR' in options:
                    file_master['parameters']['is_MCGWB_ASR_included']['value'] = 1

                # Set the parameters and assumptions related to the Desalination plant
                # ---------------------------------------------------------------------

                # Set the value below to 1 brings the IPR plant on-line (default value
                # is 0).
                if 'IPR' in options:
                    file_master['parameters']['is_IPR_included']['value'] = 1

                    # Set the parameters and assumptions related to the Indirect Potable
                    # Reuse (IPR) plant
                    # ---------------------------------------------------------------------

                    # IPR daily yield
                    file_master['parameters'][
                        'indirect_potable_reusue_plant_yield']['values'] = \
                        system_profiles.loc['IPR_yield_MGD'].tolist()

                # Set the parameters and assumptions related to the Direct Potable Reuse
                # Plant
                # ----------------------------------------------------------------------

                # Set the value below to 1 brings the DPR plat on-line (default value
                # is 0)
                if 'DPR' in options:
                    file_master['parameters']['is_DPR_included']['value'] = 1

            # Sensitivity analysis file
            # import file
            if file_SA is not None:
                with open(file_SA) as f:
                    config = json.load(f)

                file_master['parameters']['factor_demand_multiplier']['value'] = config['factor_demand_multiplier']
                file_master['parameters']['planning_inf']['filename'] = config['filename_inf_planning_assumptions']
                file_master['parameters']['cashflow_model']['filename'] = config['filename_cashflow_rate_assumptions']
                file_master['parameters']['planning_afford']['filename'] = config['filename_cashflow_rate_assumptions']

        with open('../models/{}/{}/json_models/SCWSM_P{}T{}_R{}_dCV={}_D{}_rof{}_soq{}_sv{}_mc{}_des{}.json'.
                          format(version_parent, version, dP, dT, real, dCV, demand, rof_thresh, int(rank_order[0]),
                                 int(rank_order[1]), int(rank_order[2]), int(rank_order[3])),
                  'w') as outfile_master:
            json.dump(file_master, outfile_master, indent=4)
