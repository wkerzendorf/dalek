from abc import ABCMeta, abstractmethod
from dalek.parallel.launcher import FitterLauncher, fitter_worker
import numpy as np
import logging
import sys, os

logger = logging.getLogger(__name__)

class ParameterSetConfiguration(object):
    """
    Storing the names and bounds of the parameters

    Parameters
    ----------

    parameter_names: ~list
        list of strings of parameter names

    parameter_lower_bounds: ~list or ~np.ndarray

    parameter_upper_bounds: ~list or ~np.ndarray
    """
    def __init__(self, parameter_names, parameter_lower_bounds,
                 parameter_upper_bounds):
        self.parameter_names = parameter_names
        self.parameter_lower_bounds = parameter_lower_bounds
        self.parameter_upper_bounds = parameter_upper_bounds
        assert (len(parameter_upper_bounds) == len(parameter_lower_bounds)
                == len(parameter_names))



class BaseFitter(object):
    """

    """

    def __init__(self, optimizer, remote_clients,
                 fitness_function, atom_data, default_config,
                 parameter_set_configuration, db_string=None,
                 max_iterations=50,
                 worker=fitter_worker):

        self.max_iterations = max_iterations
        self.default_config = default_config
        self.launcher = FitterLauncher(remote_clients,
                                       fitness_function, atom_data,
                                       worker)
        self.optimizer = optimizer

        if dbstring is not None:
            self.open_db(db_string)


    def open_db(self, db_string):
        pass


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
        new_parameter_collection = self.optimizer(
            evaluated_parameter_collection)
        return new_parameter_collection

    def run_fitter(self, initial_parameters):
        current_parameters = initial_parameters
        i = 0
        while i < self.max_iterations:
            logger.info('\nAt iteration {0} of {1}'.format(i,
                                                         self.max_iterations))
            current_parameters = self.run_single_fitter_iteration(
                current_parameters)

            i += 1
        self.current_parameters = self.evaluate_parameter_collection(
            current_parameters)




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
