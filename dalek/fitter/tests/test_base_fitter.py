from dalek.fitter import BaseFitter, BaseOptimizer
import numpy as np
import pandas as pd
from collections import OrderedDict
import pytest
from IPython.parallel import Client

try:
    remote_clients = Client()
except IOError:
    ipcluster_available = False
else:
    ipcluster_available = True

pytestmark = pytest.mark.skipif(not ipcluster_available,
                                reason='There is no ipython cluster running. '
                                       'Please start one with ipcluster start -n'
                                       ' <number of engines>')


class SimpleFitnessFunction(object):

    def __call__(self, config_dict):
        x = config_dict.param.x
        y = config_dict.param.y
        z = config_dict.param.z

    @staticmethod
    def fit_function(self, x, y, z):
        return (x**2 + y**2 +z**2) * np.sin(x) * np.sin(y) * np.sin(z)


class SimpleTestOptimizer(BaseOptimizer):

    def __init__(self, x_bounds, y_bounds, z_bounds, no_sets_in_collection):

        self.x_bounds = x_bounds
        self.y_bounds = y_bounds
        self.z_bounds = z_bounds

        self.no_sets_in_collection = no_sets_in_collection

    def __call__(self, param_collection):
        max_idx = param_collection.fitness.argmax()
        new_param_collection = param_collection[param_collection.index !=
                                                max_idx]
        new_x = np.random.uniform(*self.x_bounds)
        new_y = np.random.uniform(*self.y_bounds)
        new_z = np.random.uniform(*self.z_bounds)
        return new_param_collection.append(dict(('param.x', new_x),
                                                ('param.y', new_y),
                                                ('param.z', new_z)),
                                           ignore_indexing=True)

    def init_parameter_collection(self):
        x_params = np.random.uniform(self.x_bounds[0], self.x_bounds[1],
                                     self.no_sets_in_collection)

        y_params = np.random.uniform(self.x_bounds[0], self.x_bounds[1],
                                     self.no_sets_in_collection)

        z_params = np.random.uniform(self.x_bounds[0], self.x_bounds[1],
                                     self.no_sets_in_collection)

        initial_param_collection = pd.DataFrame(
            OrderedDict(('param.x', x_params), ('param.y', y_params),
                        ('param.z', z_params), ))
        initial_param_collection['fitness'] = np.nan



def test_simple_test_optimizer():
    simple_test_optimizer = SimpleTestOptimizer((-100, 100), (-100, 100),
                                                (-100, 100), 10)
    1/0

def test_simple_basefitter_instantiation():
    return
    remote_clients = None
    fitting_parameters = None
    default_config = None
    fitness_function = None
    fitter = BaseFitter(launcher, optimizer, )