
from scipy.interpolate import interp1d
import numpy as np
import calendar

from pywr.parameters import Parameter
from pywr.parameters import load_parameter


# Import the selected model run assumptions
import scwsm_model_assumptions as scwsm

        
########## UPDATE_DESALT_CAPACITY PARAMETER ##########
class UPDATE_DESALT_CAPACITY(Parameter):

    """
    This class updates the desalination_capacity_mgd parameter when more desal is built/added.
    This parameter initializes at a value of zero desal capacity.
    
    """

    def __init__(self, model, param_name, parameters):
        super().__init__(model)
        
        # add inf_time_tracker as a child
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)
            
        self.desal_mgd = 0 # initialize at zero
        
        
    def value(self, timestep, scenario_index):
        if self.model.parameters['inf_time_tracker'].get_value(scenario_index) == 1 and timestep.day == 1:
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_deploy.str.startswith('DESALT').any():
                self.desal_mgd += self.model.parameters['inf_time_tracker'].add_desal_cap()
                print('ADD DESAL CAPACITY: ', self.model.parameters['inf_time_tracker'].add_desal_cap())
            
            # if ramp down time is zero, take desal capacity offline
            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_rampdown.str.startswith('DESALT').any():
                self.desal_mgd -= self.model.parameters['inf_time_tracker'].remove_desal_cap()
                print('TURN SOME DESAL CAPACITY OFF: ', self.model.parameters['inf_time_tracker'].remove_desal_cap())
        
        return self.desal_mgd
        
    
    @classmethod
    def load(cls, model, data):
        return cls(model, **data)


########## SET_DESALT_CAPACITY_ROF PARAMETER ##########
class SET_DESALT_CAPACITY_ROF(Parameter):
    """
    This class updates the desalination_capacity_mgd parameter in the ROF model version. We need this parameter (instead
    of a constant value) so we can update it in the setup function.

    """
    def __init__(self, model):
        super().__init__(model)

        self.desal_mgd = 0  # initialize at zero

    def value(self, timestep, scenario_index):

        return self.desal_mgd

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)


class UPDATE_DESALT(Parameter):
    """
    This python class allows the boolean turning on/off desalination to be updated dynamically at each timestep.

    """

    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_desalt_included = 0

    # updated this function from just including the return statement, to update based on if we plan desal, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # make sure the time tracker is running and it's the first day of the month
        if self.model.parameters['inf_time_tracker'].get_value(scenario_index) == 1 and timestep.day == 1:
            # turn desal on
            if (self.model.parameters['inf_time_tracker'].add_desal_cap() > 0):
                self.is_desalt_included = 1

            # turn desal off
            if self.model.parameters['inf_time_tracker'].is_desal_at_end_of_life(scenario_index) and timestep.day == 1:

                print('TURN DESAL OFF')
                self.is_desalt_included = 0

        return self.is_desalt_included

    def set_desalt_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            #print('reset boolean to 0')
            self.is_desalt_included = 0
        self.is_desalt_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)

########## UPDATE_TRANSFER PARAMETER ##########
class UPDATE_TRANSFER(Parameter):
    """
    This python class allows the boolean turning on/off desalination to be updated dynamically at each timestep.

    """

    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_transfer_included = 0

    # updated this function from just including the return statement, to update based on if we plan transfer, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # TEST THIS!!!
        # if deployment time is zero, set to 1
        if self.model.parameters['inf_time_tracker'].get_value(
                scenario_index) == 1 and timestep.day == 1: 
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters['inf_time_tracker'].df_inf_deploy.isin(['TRANSFER']).any():
                print('TURN TRANSFER ON')
                self.is_transfer_included = 1

            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters['inf_time_tracker'].df_inf_rampdown.isin(['TRANSFER']).any():
                print('TURN TRANSFER OFF')
                self.is_transfer_included = 0

        return self.is_transfer_included

    def set_transfer_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            self.is_transfer_included = 0
        self.is_transfer_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)


########## UPDATE_SMASR PARAMETER ##########
class UPDATE_SMASR(Parameter):
    """
    This python class allows the boolean turning on/off ASR to be updated dynamically at each timestep.

    """

    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_smasr_included = 0

    # updated this function from just including the return statement, to update based on if we plan transfer, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # if deployment time is zero, set to 1
        if self.model.parameters['inf_time_tracker'].get_value(
                scenario_index) == 1 and timestep.day == 1:  # keep this the same
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters['inf_time_tracker'].df_inf_deploy.isin(['SMASR']).any():
                print('TURN SMASR ON')
                self.is_smasr_included = 1

            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters['inf_time_tracker'].df_inf_rampdown.isin(['SMASR']).any():
                print('TURN SMASR OFF')
                self.is_smasr_included = 0

        return self.is_smasr_included

    def set_smasr_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            self.is_smasr_included = 0
        self.is_smasr_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)

########## UPDATE_MCASR PARAMETER ##########
class UPDATE_MCASR(Parameter):
    """
    This python class allows the boolean turning on/off ASR to be updated dynamically at each timestep.

    """

    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_mcasr_included = 0

    # updated this function from just including the return statement, to update based on if we plan transfer, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # if deployment time is zero, set to 1
        if self.model.parameters['inf_time_tracker'].get_value(
                scenario_index) == 1 and timestep.day == 1:  # keep this the same
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters['inf_time_tracker'].df_inf_deploy.isin(['MCASR']).any():
                print('TURN MCASR ON')
                self.is_mcasr_included = 1

            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters['inf_time_tracker'].df_inf_rampdown.isin(['MCASR']).any():
                print('TURN MCASR OFF')
                self.is_mcasr_included = 0

        return self.is_mcasr_included

    def set_mcasr_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            self.is_mcasr_included = 0
        self.is_mcasr_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)


########## UPDATE_TRANSFER_SOQUEL PARAMETER ##########
class UPDATE_TRANSFER_SOQUEL(Parameter):
    """
    This python class allows the boolean turning on/off of transfers at Soquel to be updated dynamically at each timestep.

    """

    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_transfer_included = 0

    # updated this function from just including the return statement, to update based on if we plan transfer, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # if deployment time is zero, set to 1
        if self.model.parameters['inf_time_tracker'].get_value(
                scenario_index) == 1 and timestep.day == 1:  # keep this the same
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_deploy.isin(['TRANSFER_SOQUEL']).any():
                #print('TURN TRANSFER AT SOQUEL ON')
                self.is_transfer_included = 1

            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_rampdown.isin(['TRANSFER_SOQUEL']).any():
                self.is_transfer_included = 0

        return self.is_transfer_included

    def set_transfer_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            self.is_transfer_included = 0
        self.is_transfer_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)

########## UPDATE_TRANSFER_SCOTTS_VALLEY PARAMETER ##########
class UPDATE_TRANSFER_SCOTTS_VALLEY(Parameter):
    """
    This python class allows the boolean turning on/off of transfers at Scotts Valley to be updated dynamically at each timestep.

    """
    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_transfer_included = 0

    # updated this function from just including the return statement, to update based on if we plan transfer, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # if deployment time is zero, set to 1
        if self.model.parameters['inf_time_tracker'].get_value(
                scenario_index) == 1 and timestep.day == 1: 
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_deploy.str.contains('TRANSFER_SCOTTS_VALLEY').any():
                print('TURN TRANSFER AT SCOTTS VALLEY ON')
                self.is_transfer_included = 1

            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_rampdown.str.contains('TRANSFER_SCOTTS_VALLEY').any():
                print('TURN TRANSFER AT SCOTTS VALLEY OFF')
                self.is_transfer_included = 0

        return self.is_transfer_included

    def set_transfer_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            self.is_transfer_included = 0
        self.is_transfer_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)

########## UPDATE_DPR PARAMETER ##########
class UPDATE_DPR(Parameter):
    """
    This python class allows the boolean turning on/off for DPR to be updated dynamically at each timestep.

    """
    def __init__(self, model, param_name, parameters):
        super().__init__(model)

        # add children parameters- inf_time_tracker
        self.param_name = param_name
        self.parameters = parameters
        for parameter in self.parameters:
            self.children.add(parameter)

        self.is_dpr_included = 0

    # updated this function from just including the return statement, to update based on if we plan transfer, and then if we reach deployment or ramp down time
    def value(self, timestep, scenario_index):
        # if deployment time is zero, set to 1
        if self.model.parameters['inf_time_tracker'].get_value(
                scenario_index) == 1 and timestep.day == 1:  
            if not self.model.parameters['inf_time_tracker'].df_inf_deploy.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_deploy.str.contains('DPR').any():
                print('TURN DPR ON')
                self.is_dpr_included = 1

            if not self.model.parameters['inf_time_tracker'].df_inf_rampdown.empty and self.model.parameters[
                'inf_time_tracker'].df_inf_rampdown.str.contains('DPR').any():
                print('TURN DPR OFF')
                self.is_dpr_included = 0

        return self.is_dpr_included

    def set_transfer_boolean(self, new_value):
        if new_value != 0 and new_value != 1:
            self.is_dpr_included = 0
        self.is_dpr_included = new_value

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)
