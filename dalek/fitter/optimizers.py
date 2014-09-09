from dalek.fitter import BaseOptimizer
from dalek.parallel import ParameterCollection
import numpy as np



class LuusJaakolaOptimizer(BaseOptimizer):
    def __init__(self, fitter_configuration):
        self.fitter_configuration = fitter_configuration
        self.x = (self.fitter_configuration.lbounds +
                  self.fitter_configuration.ubounds) * 0.5
        self.n = fitter_configuration.number_of_samples
        self.d = np.array(self.fitter_configuration.ubounds -
                          self.fitter_configuration.lbounds) * 0.5

    def __call__(self, parameter_collection):
        best_fit = parameter_collection.ix[parameter_collection['dalek.fitness'].argmin()]
        best_x = best_fit.values[:-1]
        new_parameters = [best_x]
        lbounds = self.fitter_configuration.lbounds
        ubounds = self.fitter_configuration.ubounds
        for _ in range(self.n):
            new_parameters.append(np.random.uniform(np.clip(best_x - self.d, lbounds, ubounds),
                                                    np.clip(best_x + self.d, lbounds, ubounds)))
        self.d *= 0.95
        return ParameterCollection(np.array(new_parameters), columns=self.fitter_configuration.parameter_names)


