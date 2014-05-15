from abc import ABCMeta, abstractmethod
from dalek.parallel.launcher import FitterLauncher, fitter_worker


class BaseFitter(object):
    """

    """

    def __init__(self, optimizer, initial_parameters, remote_clients,
                 fitness_function, atom_data, max_iterations=50,
                 worker=fitter_worker):

        self.max_iterations = max_iterations
        self.initial_parameters = initial_parameters
        self.launcher = FitterLauncher(remote_clients,
                                       fitness_function, atom_data,
                                       worker)
        self.optimizer = optimizer


    def init_params(self):
        pass

    def run_fitter(self):
        pass

    def evaluate_parameter_collection(self, parameter_collection):
        config_dict_list = parameter_collection.to_config_dict_list()
        fitnesses_result = self.launcher.queue_parameter_set_list(
            config_dict_list)
        fitnesses_result.wait()
        parameter_collection.fitness = fitnesses_result.result

        return parameter_collection


    def run_single_fitter_iteration(self, parameter_collection):
        evaluated_parameter_collection = self.evaluate_parameter_collection(parameter_collection)
        new_parameter_collection = self.optimizer(evaluated_parameter_collection)
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


