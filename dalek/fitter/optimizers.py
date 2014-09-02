from dalek.fitter import BaseOptimizer
from dalek.parallel import ParameterCollection
import numpy as np



class LuusJaakolaOptimizer(BaseOptimizer):
    def __init__(self, fitter_configuration):
        self.fitter_configuration = fitter_configuration
        #self.x = np.array([np.random.uniform(low, high) for low, high in self.bounds])
        self.x = (self.fitter_configuration.lbounds +
                  self.fitter_configuration.ubounds) * 0.5
        self.n = fitter_configuration.number_of_samples
        self.d = np.array(self.fitter_configuration.ubounds -
                          self.fitter_configuration.lbounds) * 0.5

    def violates_boundaries(self, x):
        return any(x < self.lbound) or any(x > self.ubound)

    def __call__(self, parameter_collection):
        current_best_fit = parameter_collection.ix[
            parameter_collection['dalek.fitness'].argmin()]
        temp_parameter_collection = ParameterCollection(columns=self.fitter_configuration.parameter_names)
        
        for i, param_name in enumerate(self.fitter_configuration.parameter_names):
            
            temp_parameter_collection[param_name] = np.random.uniform(max(-self.d[i] + current_best_fit.values[i], 
                                  self.fitter_configuration.lbounds[i]),
                              min(self.d[i] + current_best_fit.values[i], 
                                  self.fitter_configuration.ubounds[i]), 
                              size=self.n - 1)
        new_parameter_collection = ParameterCollection(current_best_fit.values[None], columns=parameter_collection.columns).append(temp_parameter_collection, ignore_index=True)
        self.d *= 0.95
        return new_parameter_collection

