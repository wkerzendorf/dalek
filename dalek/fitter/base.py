from abc import ABCMeta, abstractmethod
from dalek.parallel.launcher import FitterLauncher, fitter_worker
from dalek.fitter.optimizers import optimizer_dict as all_optimizer_dict
from dalek.fitter.fitness_function import fitness_function_dict as all_fitness_function_dict
import numpy as np
from tardis.io.config_reader import ConfigurationNameSpace
from tardis.atomic import AtomData
import logging
import sys, os
import yaml
from collections import OrderedDict


from dalek.parallel.parameter_collection import ParameterCollection


logger = logging.getLogger(__name__)


import yaml
import yaml.constructor

try:
    # included in standard lib from Python 2.7
    from collections import OrderedDict
except ImportError:
    # try importing the backported drop-in replacement
    # it's available on PyPI
    from ordereddict import OrderedDict

class OrderedDictYAMLLoader(yaml.Loader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping



class FitterConfiguration(object):
    """
    Storing the names and bounds of the parameters

    Parameters
    ----------

    parameter_names: ~list
        list of strings of parameter names

    parameter_lower_bounds: ~list or ~np.ndarray

    parameter_upper_bounds: ~list or ~np.ndarray

    parameter_types: ~list of ~str
        list of allowed sqlalchemy parameter types (i.e. integer, float, string)

    default_config: ~tardis.io.config_reader.ConfigurationNameSpace
        the default config

    generate_initial_paramater_collection:
    """


    @classmethod
    def from_yaml(cls, fname):
        """
        Reading the fitter configuration from a yaml file
        
        Parameters
        ----------
        
        """

        conf_dict = yaml.load(open(fname), OrderedDictYAMLLoader)
        default_config = ConfigurationNameSpace.from_yaml(
            conf_dict['tardis']['default_conf'])
        atom_data = AtomData.from_hdf5(conf_dict['tardis']['atom_data'])
        parameter_config = ParameterConfiguration.from_conf_dict(conf_dict['fitter']['parameters'])

        number_of_samples = conf_dict['fitter']['number_of_samples']
        max_iterations = conf_dict['fitter']['max_iterations']
        optimizer_dict = conf_dict['fitter'].pop('optimizer')
        optimizer = all_optimizer_dict[optimizer_dict.pop('name')]
        fitness_function_dict = optimizer['fitter'].pop('fitness_function')
        fitness_function_class = all_fitness_function_dict[
            fitness_function_dict.pop('name')]
        fitness_function = fitness_function_class.from_config_dict(
            fitness_function_dict)

        return cls(optimizer, fitness_function,
                   parameter_config=parameter_config,
                   default_config=default_config, atom_data=atom_data,
                   number_of_samples=number_of_samples,
                   max_iterations=max_iterations)



        
        

    def __init__(self, optimizer, fitness_function, parameter_config, default_config,
                 atom_data, number_of_samples, max_iterations=50,
                 generate_initial_parameter_collection=None, optimizer_config={}):
        self.optimizer = optimizer
        self.fitness_function = fitness_function
        self.parameter_config = parameter_config

        self.default_config = default_config
        self.max_iterations = max_iterations
        self.atom_data = atom_data
        self.number_of_samples = number_of_samples
        self.generate_initial_parameter_collection = \
            generate_initial_parameter_collection
        self.optimizer_config = optimizer_config


    @property
    def all_parameter_names(self):
        return self.parameter_names + self.fitter_parameter_names

    @property
    def all_parameter_types(self):
        return self.parameter_types + self.fitter_parameter_types

    def get_initial_parameter_collection(self, number_of_samples=None):
        """
        Generate initial ParameterCollection

        Returns
        -------

        initial_parameter_collection : ~dalek.parallel.ParameterCollection


        """

        if number_of_samples is None:
            number_of_samples = self.number_of_samples

        if self.generate_initial_parameter_collection is not None:
            return self.generate_initial_parameter_collection(number_of_samples=
                                                              number_of_samples)
        initial_data = np.array([np.random.uniform(lbound, ubound,
                                          size=number_of_samples)
                        for lbound, ubound in self.parameter_bounds])
        return ParameterCollection(initial_data.T, columns=self.parameter_names)



class ParameterConfiguration(object):
    """
    Configuration of the different Parameters

    Parameters
    ----------

    parameter_names: ~list of ~str

    parameter_bounds: ~list of ~tuple


    """
    @classmethod
    def from_conf_dict(cls, parameter_conf_dict):
        parameter_names = parameter_conf_dict.keys()
        parameter_bounds = [parameter_conf_dict[param]['bounds']
                            for param in parameter_names]
        return cls(parameter_names, parameter_bounds)

    def __init__(self, parameter_names, parameter_bounds):

        self.parameter_names = parameter_names
        self.parameter_bounds = np.array(parameter_bounds)

        assert len(parameter_bounds) == len(parameter_names)


    @property
    def lbounds(self):
        return self.parameter_bounds[:,0]

    @property
    def ubounds(self):
        return self.parameter_bounds[:,1]


class BaseFitter(object):
    """
    Basic fitter class for Dalek

    Parameters
    ----------


    """

    def __init__(self, remote_clients,
                 fitter_configuration, parameter_log=None,
                 worker=fitter_worker):

        self.fitter_configuration = fitter_configuration
        self.default_config = fitter_configuration.default_config

        self.launcher = FitterLauncher(
            remote_clients, self.fitter_configuration.fitness_function,
            fitter_configuration.atom_data, worker)

        self.optimizer = self.fitter_configuration.optimizer
        
        self.big_parameter_collection = None
        self.parameter_log = parameter_log



    def evaluate_parameter_collection(self, parameter_collection):
        config_dict_list = parameter_collection.to_config(self.default_config)
        fitnesses_result = self.launcher.queue_parameter_set_list(
            config_dict_list)

        while fitnesses_result.progress < len(fitnesses_result):
            fitnesses_result.wait(timeout=1)
            sys.stdout.write('\r{0}/{1} TARDIS runs done for current iteration'.format(
                fitnesses_result.progress, len(fitnesses_result)))
            sys.stdout.flush()
        fitnesses = zip(*fitnesses_result.result)[0]
        self.spectra = zip(*fitnesses_result.result)[1]
        parameter_collection['dalek.fitness'] = fitnesses

        return parameter_collection


    def run_single_fitter_iteration(self, parameter_collection):
        evaluated_parameter_collection = self.evaluate_parameter_collection(
            parameter_collection)
        if self.big_parameter_collection is None:
            self.big_parameter_collection = evaluated_parameter_collection.copy()
        else:
            self.big_parameter_collection = self.big_parameter_collection.append(
                evaluated_parameter_collection, ignore_index=True)
        new_parameter_collection = self.optimizer(
            evaluated_parameter_collection)
        return new_parameter_collection

    def run_fitter(self, initial_parameters):
        self.current_parameters = initial_parameters

        i = 0
        while i < self.fitter_configuration.max_iterations:
            logger.info('\nAt iteration {0} of {1}'.format(i,
                                                           self.
                                                           fitter_configuration.
                                                           max_iterations))
            self.current_parameters = self.run_single_fitter_iteration(
                self.current_parameters)
            if self.parameter_log is not None:
                self.big_parameter_collection.to_csv(self.parameter_log)

            i += 1
        
            

