from abc import ABCMeta, abstractmethod


def simple_rms_worker():
    pass

class BaseFitter(object):
    """

    """

    def __init__(self, optimizer, launcher, initial_parameters, max_iterations=50):
        self.max_iterations = max_iterations
        self.initial_parameters = initial_parameters
        pass

    def init_params(self):
        pass

    def run_fitter(self):
        pass

    def evaluate_parameter_collection(self):
        pass

    def run_single_fitter_iteration(self, parameter_collection):

        evaluated_parameter_collection = self.evaluate_parameter_collection(parameter_collection)
        new_parameter_collection = self.optimizer(evaluated_parameter_collection)
        return new_parameter_collection

    def run_fitter(self):
        current_parameters = initial_parameters
        i = 0
        while True:
            if i > self.max_iterations:
                break

            current_parameters = self.run_single_fitter_iteration(
                current_parameters)

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


