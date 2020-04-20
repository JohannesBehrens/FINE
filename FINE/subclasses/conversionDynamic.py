from FINE.conversion import Conversion, ConversionModel
from FINE import utils
import pyomo.environ as pyomo
import pandas as pd

import warnings


class ConversionDynamic(Conversion):
    """
    Extension of the conversion class with more specific ramping behavior
    """
    def __init__(self, esM, name, physicalUnit, commodityConversionFactors, downTimeMin=None, 
                 upTimeMin=None, rampUpMax =None, rampDownMax=None, **kwargs):
        """
        Constructor for creating a ConversionDynamic class instance.
        The ConversionDynamic component specific input arguments are described below. The Conversion
        specific input arguments are described in the Conversion class and the general component
        input arguments are described in the Component class.

        **Default arguments:**
        :param downTimeMin: if specified, indicates minimal down time of the component [number of time steps]. 
            |br| * the default value is None
        :type downTimeMin:
            * None or
            * Integer value in range ]0,numberOfTimeSteps]

        :param upTimeMin: if specified, indicates minimal up time of the component [number of time steps]. 
            |br| * the default value is None
        :type upTimeMin:
            * None or
            * Integer value in range ]0,numberOfTimeSteps]

        :param rampUpMax: A maximum ramping rate to limit the increase in the operation of the component as share of the installed capacity.
            |br| * the default value is None
        :type rampUpMax:
            * None or
            * Float value in range ]0.0,1.0]

        :param rampDownMax: A maximum ramping rate to limit the decrease in the operation of the component as share of the installed capacity.
            |br| * the default value is None
        :type rampDownMax:
            * None or
            * Float value in range ]0.0,1.0]

        :param **kwargs: All other keyword arguments of the conversion class can be defined as well.
        :type kwargs:
            * Check Conversion Class documentation.
        """
        Conversion.__init__(self, esM, name, physicalUnit, commodityConversionFactors, **kwargs)

        self.modelingClass = ConversionDynamicModel
        self.downTimeMin = downTimeMin
        self.upTimeMin = upTimeMin
        self.rampUpMax =rampUpMax
        self.rampDownMax = rampDownMax
        utils.checkConversionDynamicSpecficDesignInputParams(self, esM)

    def setTimeSeriesData(self, hasTSA):
        """
        Function for setting the maximum operation rate and fixed operation rate depending on whether a time series
        analysis is requested or not.

        :param hasTSA: states whether a time series aggregation is requested (True) or not (False).
        :type hasTSA: boolean
        """
        super().setTimeSeriesData(hasTSA)
        if hasTSA:
            warnings.warn('Class "ConversionDynamic" works only partially together with "timeSeriesAggregation"' 
                    + ', since the dynamic constraints between typical periods are relaxed.')
        return
        



class ConversionDynamicModel(ConversionModel):

    """
    A ConversionDynamicModel class instance will be instantly created if a ConversionDynamic class instance is initialized.
    It is used for the declaration of the sets, variables and constraints which are valid for the ConversionDynamic
    class instance. These declarations are necessary for the modeling and optimization of the energy system model.
    The ConversionDynamicModel class inherits from the ConversionModel class. """

    def __init__(self):
        self.abbrvName = 'conv_dyn'
        self.dimension = '1dim'
        self.componentsDict = {}
        self.capacityVariablesOptimum, self.isBuiltVariablesOptimum = None, None
        self.operationVariablesOptimum = None
        self.optSummary = None
        
    ####################################################################################################################
    #                                            Declare sparse index sets                                             #
    ####################################################################################################################

    def declareOperationStartStopBinarySet(self, pyM):
        """
        Declare operation related sets for binary decicion variables (operation variables) in the pyomo object for a
        modeling class. This reflects the starting or stopping state of the conversion component.        
        
        :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
        :type pyM: pyomo ConcreteModel  
        """
        compDict, abbrvName = self.componentsDict, self.abbrvName
        def declareOperationBinarySet(pyM):
            return ((loc, compName) for compName, comp in compDict.items() 
                for loc in comp.locationalEligibility.index if comp.locationalEligibility[loc] == 1)
        setattr(pyM, 'operationVarStartStopSetBin_' + abbrvName, pyomo.Set(dimen=2, initialize=declareOperationBinarySet))
        
        
    def declareOpConstrSetMinDownTime(self, pyM, constrSetName):
        """
        Declare set of locations and components for which downTimeMin is not None.
        """
        compDict, abbrvName = self.componentsDict, self.abbrvName
        varSet = getattr(pyM, 'operationVarStartStopSetBin_' + abbrvName)

        def declareOpConstrSetMinDownTime(pyM):
            return ((loc, compName) for loc, compName in varSet if getattr(compDict[compName], 'downTimeMin') is not None)

        setattr(pyM, constrSetName + 'downTimeMin_' + abbrvName, pyomo.Set(dimen=2, initialize=declareOpConstrSetMinDownTime))
    
    
    def declareOpConstrSetMinUpTime(self, pyM, constrSetName):
        """
        Declare set of locations and components for which upTimeMin is not None.
        """
        compDict, abbrvName = self.componentsDict, self.abbrvName
        varSet = getattr(pyM, 'operationVarStartStopSetBin_' + abbrvName)

        def declareOpConstrSetMinUpTime(pyM):
            return ((loc, compName) for loc, compName in varSet if getattr(compDict[compName], 'upTimeMin') is not None)

        setattr(pyM, constrSetName + 'upTimeMin_' + abbrvName, pyomo.Set(dimen=2, initialize=declareOpConstrSetMinUpTime))
        
    def declareOpConstrSetMaxRampUp(self, pyM, constrSetName):
        """
        Declare set of locations and components for which rampUpMax is not None.
        """
        compDict, abbrvName = self.componentsDict, self.abbrvName
        varSet = getattr(pyM, 'operationVarSet_' + abbrvName)


        def declareOpConstrSetMaxRampUp(pyM):
           return ((loc, compName) for loc, compName in varSet if getattr(compDict[compName], 'rampUpMax') is not None)

        setattr(pyM, constrSetName + 'rampUpMax_' + abbrvName, pyomo.Set(dimen=2, initialize=declareOpConstrSetMaxRampUp))

    def declareOpConstrSetMaxRampDown(self, pyM, constrSetName):
        """
        Declare set of locations and components for which rampDownMax is not None.
        """
        compDict, abbrvName = self.componentsDict, self.abbrvName
        varSet = getattr(pyM, 'operationVarSet_' + abbrvName)


        def declareOpConstrSetMaxRampDown(pyM):
           return ((loc, compName) for loc, compName in varSet if getattr(compDict[compName], 'rampDownMax') is not None)

        setattr(pyM, constrSetName + 'rampDownMax_' + abbrvName, pyomo.Set(dimen=2, initialize=declareOpConstrSetMaxRampDown))

        
    def declareSets(self, esM, pyM):
        """
        Declare sets and dictionaries: design variable sets, operation variable set, operation mode sets and
        linked components dictionary.

        :param esM: EnergySystemModel instance representing the energy system in which the component should be modeled.
        :type esM: esM - EnergySystemModel class instance

        :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
        :type pyM: pyomo ConcreteModel
        """
        super().declareSets(esM, pyM)

        # Declare operation variable sets
        self.declareOperationStartStopBinarySet(pyM)

        # Declare Min down time constraint
        self.declareOpConstrSetMinDownTime(pyM, 'opConstrSet')
        self.declareOpConstrSetMinUpTime(pyM, 'opConstrSet')
        self.declareOpConstrSetMaxRampUp(pyM, 'opConstrSet')
        self.declareOpConstrSetMaxRampDown(pyM, 'opConstrSet')
        
   
    ####################################################################################################################
    #                                                Declare variables                                                 #
    ####################################################################################################################

    def declareStartStopVariables(self, pyM):
        """
        Declare start/stop variables.

        :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
        :type pyM: pyomo Concrete Model
        """
        setattr(pyM, 'startVariable_' + self.abbrvName,
                pyomo.Var(getattr(pyM, 'operationVarStartStopSetBin_' + self.abbrvName), pyM.timeSet, domain=pyomo.Binary))
        
        setattr(pyM, 'stopVariable_' + self.abbrvName,
                pyomo.Var(getattr(pyM, 'operationVarStartStopSetBin_' + self.abbrvName), pyM.timeSet, domain=pyomo.Binary))
        

    def declareVariables(self, esM, pyM, relaxIsBuiltBinary):
        """
        Declare design and operation variables

        :param esM: EnergySystemModel instance representing the energy system in which the component should be modeled.
        :type esM: esM - EnergySystemModel class instance

        :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
        :type pyM: pyomo ConcreteModel
        """
        super().declareVariables(esM, pyM, relaxIsBuiltBinary)
               
        self.declareStartStopVariables(pyM)
        

    ####################################################################################################################
    #                                          Declare component constraints                                           #
    ####################################################################################################################

    def minimumDownTime(self, pyM, esM):
        """
        Ensure that conversion unit is not ramping up and down too often by implementing a minimum down time after ramping down.
        

        :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
        :type pyM: pyomo Concrete Model
        """
        compDict, abbrvName = self.componentsDict, self.abbrvName
        
        opVarBin= getattr(pyM, 'op_bin_' + abbrvName)
        opVarStartBin, opVarStopBin = getattr(pyM, 'startVariable_' + abbrvName), getattr(pyM, 'stopVariable_' + abbrvName)
        constrSetMinDownTime = getattr(pyM,'opConstrSet' + 'downTimeMin_' + abbrvName)
        numberOfTimeSteps = len(esM.timeStepsPerPeriod)

        def minimumDownTime1(pyM, loc, compName, p, t):
            if t>=1:
                return (opVarBin[loc, compName, p, t]-opVarBin[loc, compName, p, t-1]-opVarStartBin[loc, compName, p, t]+opVarStopBin[loc, compName, p, t] == 0)
            else:
                return (opVarBin[loc, compName, p, t]-opVarBin[loc, compName, p, numberOfTimeSteps-1]-opVarStartBin[loc, compName, p, t] \
                + opVarStopBin[loc, compName, p, t] == 0)
        setattr(pyM, 'ConstrMinDownTime1_' + abbrvName, pyomo.Constraint(constrSetMinDownTime, pyM.timeSet, rule=minimumDownTime1))
          
        def minimumDownTime2(pyM, loc, compName, p, t):
            downTimeMin = getattr(compDict[compName], 'downTimeMin')
            if t >= downTimeMin:
                return opVarBin[loc, compName, p, t] <= 1 -pyomo.quicksum(opVarStopBin[loc, compName, p, t_down] for t_down in range(t-downTimeMin+1, t))
            else:
                return opVarBin[loc, compName, p, t] <= 1 -pyomo.quicksum(opVarStopBin[loc, compName, p, t_down] for t_down in range(0, t)) \
                    - pyomo.quicksum(opVarStopBin[loc, compName, p, t_down] for t_down in range(numberOfTimeSteps-(downTimeMin-t), numberOfTimeSteps))

        setattr(pyM, 'ConstrMinDownTime2_' + abbrvName, pyomo.Constraint(constrSetMinDownTime, pyM.timeSet, rule=minimumDownTime2))          
                    
    def minimumUpTime(self, pyM, esM):
            """
            Ensure that conversion unit is not ramping up and down too often by implementing a minimum up time after ramping up.
            

            :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
            :type pyM: pyomo Concrete Model
            """
            compDict, abbrvName = self.componentsDict, self.abbrvName
            
            opVarBin= getattr(pyM, 'op_bin_' + abbrvName)
            opVarStartBin, opVarStopBin = getattr(pyM, 'startVariable_' + abbrvName), getattr(pyM, 'stopVariable_' + abbrvName)
            constrSetMinUpTime = getattr(pyM,'opConstrSet' + 'upTimeMin_' + abbrvName)
            numberOfTimeSteps = len(esM.timeStepsPerPeriod)
    
            def minimumUpTime1(pyM, loc, compName, p, t):
                downTimeMin = getattr(compDict[compName], 'downTimeMin')
                if (t>=1 and downTimeMin==None): # avoid to set constraints twice
                    return (opVarBin[loc, compName, p, t]-opVarBin[loc, compName, p, t-1]-opVarStartBin[loc, compName, p, t]+opVarStopBin[loc, compName, p, t] == 0)
                else:
                    return (opVarBin[loc, compName, p, t]-opVarBin[loc, compName, p, numberOfTimeSteps-1]-opVarStartBin[loc, compName, p, t] \
                        + opVarStopBin[loc, compName, p, t] == 0)
            setattr(pyM, 'ConstrMinUpTime1_' + abbrvName, pyomo.Constraint(constrSetMinUpTime, pyM.timeSet, rule=minimumUpTime1))
              
            def minimumUpTime2(pyM, loc, compName, p, t):
                upTimeMin = getattr(compDict[compName], 'upTimeMin')
                if t >= upTimeMin:
                    return opVarBin[loc, compName, p, t] >= pyomo.quicksum(opVarStartBin[loc, compName, p, t_up] for t_up in range(t-upTimeMin+1, t))
                else:
                    return opVarBin[loc, compName, p, t] >= pyomo.quicksum(opVarStartBin[loc, compName, p, t_up] for t_up in range(0, t)) \
                        + pyomo.quicksum(opVarStartBin[loc, compName, p, t_up] for t_up in range(numberOfTimeSteps-(upTimeMin-t), numberOfTimeSteps))
    
            setattr(pyM, 'ConstrMinUpTime2_' + abbrvName, pyomo.Constraint(constrSetMinUpTime, pyM.timeSet, rule=minimumUpTime2))    
    
    
    def rampUpMax(self, pyM, esM):
            """
            Ensure that conversion unit is not ramping up too fast by implementing a maximum ramping rate as share of the installed capacity.
            

            :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
            :type pyM: pyomo Concrete Model
            """
            compDict, abbrvName = self.componentsDict, self.abbrvName
            
            opVar= getattr(pyM, 'op_' + abbrvName)
            capVar= getattr(pyM, 'cap_' + abbrvName)
            
            constrSetRampUpMax = getattr(pyM,'opConstrSet' + 'rampUpMax_' + abbrvName)
            numberOfTimeSteps = len(esM.timeStepsPerPeriod)
    
            def rampUpMax(pyM, loc, compName, p, t):
                rampRateMax = getattr(compDict[compName], 'rampUpMax')
                if (t>=1): # avoid to set constraints twice
                    return (opVar[loc, compName, p, t]-opVar[loc, compName, p, t-1] <= rampRateMax*capVar[loc, compName])
                else:
                    return (opVar[loc, compName, p, t]-opVar[loc, compName, p, numberOfTimeSteps-1] <= rampRateMax*capVar[loc, compName])
            setattr(pyM, 'ConstrRampUpMax_' + abbrvName, pyomo.Constraint(constrSetRampUpMax, pyM.timeSet, rule=rampUpMax))
              
    def rampDownMax(self, pyM, esM):
            """
            Ensure that conversion unit is not ramping down too fast by implementing a maximum ramping rate as share of the installed capacity.
            
    
            :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
            :type pyM: pyomo Concrete Model
            """
            compDict, abbrvName = self.componentsDict, self.abbrvName
            
            opVar= getattr(pyM, 'op_' + abbrvName)
            capVar= getattr(pyM, 'cap_' + abbrvName)
            
            constrSetRampDownMax = getattr(pyM,'opConstrSet' + 'rampDownMax_' + abbrvName)
            numberOfTimeSteps = len(esM.timeStepsPerPeriod)
    
            def rampDownMax(pyM, loc, compName, p, t):
                rampRateMax = getattr(compDict[compName], 'rampDownMax')
                if (t>=1): # avoid to set constraints twice
                    return (opVar[loc, compName, p, t-1]-opVar[loc, compName, p, t] <= rampRateMax*capVar[loc, compName])
                else:
                    return (opVar[loc, compName, p, numberOfTimeSteps-1]-opVar[loc, compName, p, t] <= rampRateMax*capVar[loc, compName])
            setattr(pyM, 'ConstrRampDownMax_' + abbrvName, pyomo.Constraint(constrSetRampDownMax, pyM.timeSet, rule=rampDownMax))
                    
    
    
    def declareComponentConstraints(self, esM, pyM):
        """
        Declare time independent and dependent constraints.

        :param esM: EnergySystemModel instance representing the energy system in which the component should be modeled.
        :type esM: EnergySystemModel class instance

        :param pyM: pyomo ConcreteModel which stores the mathematical formulation of the model.
        :type pyM: pyomo Concrete Model
        """
        super().declareComponentConstraints(esM, pyM)

        ################################################################################################################
        #                                         Dynamic Constraints                                                  #
        ################################################################################################################
        self.minimumDownTime(pyM, esM)
        self.minimumUpTime(pyM, esM)
        self.rampUpMax(pyM, esM)
        self.rampDownMax(pyM, esM)
        
