from abc import ABCMeta, abstractmethod
from dalek.parallel.launcher import FitterLauncher, fitter_worker
import numpy as np
import pandas as pd
import logging
import sys, os


from dalek.parallel.parameter_collection import ParameterCollection


logger = logging.getLogger(__name__)

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
    def from_yaml(cls):
        pass

    def __init__(self, parameter_names, parameter_bounds, default_config,
                 atom_data, number_of_samples, max_iterations=50,
                 generate_initial_parameter_collection=None):
        self.parameter_names = parameter_names
        self.parameter_bounds = np.array(parameter_bounds)

        assert len(parameter_bounds) == len(parameter_names)

        self.default_config = default_config
        self.max_iterations = max_iterations
        self.atom_data = atom_data
        self.number_of_samples = number_of_samples
        self.generate_initial_parameter_collection = \
            generate_initial_parameter_collection

    @property
    def lbounds(self):
        return self.parameter_bounds[:,0]

    @property
    def ubounds(self):
        return self.parameter_bounds[:,1]

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

"""
    def get_alchemy_table(self, metadata, table_name='dalek_parameter_sets',
                          name_mangling=lambda column_string:
                          column_string.replace('.', '__')):

        ""
        Generate a sqlalchemy table structure

        Parameters
        ----------

        table_name: ~str
            string of table name

        metadata
        ""
        columns = [Column('id', Integer, primary_key=True)]
        columns += [Column(name_mangling(column_name), column_type)
                    for column_name, column_type in
                    zip(self.all_parameter_names, self.all_parameter_types)]

        return Table(table_name, metadata, *columns)

"""


class BaseFitter(object):
    """
    Basic fitter class for Dalek

    Parameters
    ----------


    """

    def __init__(self, remote_clients, optimizer, fitness_function,
                 fitter_configuration, parameter_log=None,
                 worker=fitter_worker):

        self.fitter_configuration = fitter_configuration
        self.default_config = fitter_configuration.default_config

        self.launcher = FitterLauncher(remote_clients, fitness_function,
                                       fitter_configuration.atom_data, worker)
        self.optimizer = optimizer(fitter_configuration)
        
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

        parameter_collection['dalek.fitness'] = fitnesses_result.result

        return parameter_collection


    def run_single_fitter_iteration(self, parameter_collection):
        evaluated_parameter_collection = self.evaluate_parameter_collection(
            parameter_collection)
        if self.big_parameter_collection is None:
            self.big_parameter_collection = evaluated_parameter_collection.copy()
        else:
            self.big_parameter_collection = self.big_parameter_collection.append(evaluated_paramter_collection, ignore_index=True)
        new_parameter_collection = self.optimizer(
            evaluated_parameter_collection)
        return new_parameter_collection

    def run_fitter(self, initial_parameters):
        current_parameters = initial_parameters

        i = 0
        while i < self.fitter_configuration.max_iterations:
            logger.info('\nAt iteration {0} of {1}'.format(i,
                                                           self.
                                                           fitter_configuration.
                                                           max_iterations))
            self.current_parameters = self.run_single_fitter_iteration(
                current_parameters)
            if self.parameter_log is not None:
                self.big_parameter_collection.to_csv(self.parameter_log)

            i += 1
        
            



class BaseOptimizer(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class BaseFitnessFunction(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class SimpleRMSFitnessFunction(BaseFitnessFunction):
    def __init__(self, observed_spectrum_wavelength, observed_spectrum_flux):
        self.observed_spectrum_wavelength = observed_spectrum_wavelength
        self.observed_spectrum_flux = observed_spectrum_flux

    def __call__(self, radial1d_mdl):

        if radial1d_mdl.spectrum_virtual.flux_nu.sum() > 0:
            synth_spectrum = radial1d_mdl.spectrum_virtual
        else:
            synth_spectrum = radial1d_mdl.spectrum
        synth_spectrum_flux = np.interp(self.observed_spectrum_wavelength,
                                        synth_spectrum.wavelength.value,
                                        synth_spectrum.flux_lambda.value)

        fitness = np.sum((synth_spectrum_flux -
                          self.observed_spectrum_flux) ** 2)

        return fitness
