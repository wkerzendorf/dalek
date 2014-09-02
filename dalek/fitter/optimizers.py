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
        self.d = np.array(self.fitter_configuration.lbounds -
                          self.fitter_configuration.lbounds) * 0.5

    def violates_boundaries(self, x):
        return any(x < self.lbound) or any(x > self.ubound)

    def __call__(self, parameter_collection):
        self.ys = parameter_collection['dalek.fitness']
        self.x, self.y = min(zip(self.xs, self.ys), key=lambda pair: pair[1])
        self.d *= 0.95
        xs = []
        for _ in range(self.n):
            a = np.random.uniform(-self.d, self.d)
            x_ = self.x + a
            while self.violates_boundaries(x_):
                a = np.random.uniform(-self.d, self.d)
                x_ = self.x + a
            xs.append(x_)
        self.xs = np.array(xs)
        xs = np.array(xs)
        return ParameterCollection(xs, columns=parameter_collection.columns)
