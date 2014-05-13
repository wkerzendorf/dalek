from abc import ABCMeta, abstractmethod


def simple_rms_worker():
    pass

class BaseFitter(object):
    """

    """

    def __init__(self, optimizer, initial_parameters=None):
        pass

    def init_params(self):
        pass

    def run_fitter(self):
        pass

    def evaluate_points(self):
        pass



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


