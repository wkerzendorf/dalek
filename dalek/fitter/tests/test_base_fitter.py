from dalek.fitter import BaseFitter, BaseOptimizer
from dalek.parallel.parameter_collection import ParameterCollection2
from dalek.parallel.launcher import FitterLauncher
import numpy as np
import pandas as pd
from collections import OrderedDict
import pytest
from IPython.parallel import Client, interactive


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


class ParameterTestCollection(ParameterCollection2):
    def to_config_dict_list(self):
        config_dict_list = []
        for idx, row in self.iterrows():
            current_config_dict = row.to_dict()
            fitness = current_config_dict.pop('fitness')
            config_dict_list.append(current_config_dict)

        return config_dict_list


class SimpleFitnessFunction(object):

    def __call__(self, config_dict):
        x = config_dict['param.x']
        y = config_dict['param.y']
        z = config_dict['param.z']

        return self.fit_function(x, y, z)

    @staticmethod
    def fit_function(x, y, z):
        return (x**2 + y**2 +z**2) * np.sin(x) * np.sin(y) * np.sin(z)


class SimpleTestOptimizer(BaseOptimizer):

    def __init__(self, x_bounds, y_bounds, z_bounds, no_sets_in_collection):

        self.x_bounds = x_bounds
        self.y_bounds = y_bounds
        self.z_bounds = z_bounds

        self.no_sets_in_collection = no_sets_in_collection

    def __call__(self, param_collection):

        if np.any(param_collection.fitness == np.nan):
            raise ValueError
        max_idx = param_collection.fitness.argmax()
        new_param_collection = param_collection[param_collection.index !=
                                                max_idx]
        1/0
        new_x = np.random.uniform(*self.x_bounds)
        new_y = np.random.uniform(*self.y_bounds)
        new_z = np.random.uniform(*self.z_bounds)
        return new_param_collection.append(dict([('param.x', new_x),
                                                ('param.y', new_y),
                                                ('param.z', new_z)]),
                                           ignore_index=True)

    def init_parameter_collection(self):
        x_params = np.random.uniform(self.x_bounds[0], self.x_bounds[1],
                                     self.no_sets_in_collection)

        y_params = np.random.uniform(self.x_bounds[0], self.x_bounds[1],
                                     self.no_sets_in_collection)

        z_params = np.random.uniform(self.x_bounds[0], self.x_bounds[1],
                                     self.no_sets_in_collection)

        initial_param_collection = ParameterTestCollection(
            OrderedDict([('param.x', x_params), ('param.y', y_params),
                        ('param.z', z_params)]))
        initial_param_collection['fitness'] = np.nan
        return initial_param_collection


@interactive
def fitter_test_worker(config_dict, atom_data=None):
    """
    This is a TARDIS worker that will run TARDIS and evaluate the returned model
    by running the pushed fitness_function object

    Parameters
    ----------

    config_dict: ~dict
        a valid TARDIS config dictionary

    """

    return fitness_function(config_dict)



class TestSimpleBaseFitter(object):

    def setup(self):
        np.random.seed(250880)
        self.simple_test_optimizer = SimpleTestOptimizer((-100, 100), (-100, 100),
                                                    (-100, 100), 10)
        self.initial_parameters = self.simple_test_optimizer.init_parameter_collection()

        self.simple_test_fitness_function = SimpleFitnessFunction()

        self.launcher = FitterLauncher(remote_clients,
                                       self.simple_test_fitness_function, None,
                                       fitter_test_worker)



    def test_initial_parameters(self):
        assert (self.initial_parameters.columns.values.tolist() ==
                ['param.x', 'param.y', 'param.z', 'fitness'])

    def test_simple_basefitter(self):
        1/0
