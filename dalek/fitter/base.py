from abc import ABCMeta, abstractmethod
from dalek.parallel.launcher import FitterLauncher, fitter_worker
import numpy as np
import logging
import sys

logger = logging.getLogger(__name__)

class BaseFitter(object):
    """

    """

    def __init__(self, optimizer, remote_clients,
                 fitness_function, atom_data, default_config, max_iterations=50,
                 worker=fitter_worker):

        self.max_iterations = max_iterations
        self.default_config = default_config
        self.launcher = FitterLauncher(remote_clients,
                                       fitness_function, atom_data,
                                       worker)
        self.optimizer = optimizer


    def evaluate_parameter_collection(self, parameter_collection):
        config_dict_list = parameter_collection.to_config(self.default_config)
        fitnesses_result = self.launcher.queue_parameter_set_list(
            config_dict_list)
        print "\n"
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
        while True:
            if i > self.max_iterations:
                break

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
        try:
            synth_spectrum = radial1d_mdl.virtual_spectrum
        except AttributeError:
            synth_spectrum = radial1d_mdl.spectrum
        synth_spectrum_flux = np.interp(self.observed_spectrum_wavelength.value,
                                        synth_spectrum.wavelength.value,
                                        synth_spectrum.flux_lambda.value)
        fitness = np.sum((synth_spectrum_flux - self.observed_spectrum_flux) ** 2)
        return fitness
"""
class SimpleRandomSearch(BaseOptimizer):
    
    def __init__(self, parameter_names, parameter_bounds, no_parameter_sets, *args, **kwargs):
        # parameter_names can be anything like ['model.abundances.C', 'supernova.luminosity_requested', ...]
        #use this to do certain settings in regards to the optimizer behaviour
        #e.g. setting which parameters to optimize
        
        self.parameter_names = parameter_names
        self.parameter_bounds = parameter_bounds
        self.no_parameter_sets = no_parameter_sets
    
    def __call__(self, parameter_collection)
    
        parameter_collection['model.abundances.Fe'] -> array
        parameter_collection['dalek.fitness'] -> 
        # generate the next parameter collection
        new_parameter_collection = generate(parameter_collection)
        return new_parameter_collection
    
    def init_parameter_collection(self):
        parameters_sets = {'model.abundances.C':[0.2, 0.3, 0.5], 'model.abundances.Fe' : [0.1, 0.3, 0.5]}
        return ParameterCollection(parameter_sets)
"""