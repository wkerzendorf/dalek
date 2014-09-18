from abc import ABCMeta, abstractmethod

class BaseFitnessFunction(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class SimpleRMSFitnessFunction(BaseFitnessFunction):

    @classmethod
    def from_config_dict(cls, conf_dict):
        pass

    def __init__(self, observed_spectrum):
        self.observed_spectrum = observed_spectrum
        self.observed_spectrum_wavelength = observed_spectrum.wavelength
        self.observed_spectrum_flux = observed_spectrum.flux

    def __call__(self, radial1d_mdl):

        if radial1d_mdl.spectrum_virtual.flux_nu.sum() > 0:
            synth_spectrum = radial1d_mdl.spectrum_virtual
        else:
            synth_spectrum = radial1d_mdl.spectrum
        synth_spectrum_flux = np.interp(self.observed_spectrum_wavelength,
                                        synth_spectrum.wavelength.value[::-1],
                                        synth_spectrum.flux_lambda.value[::-1])

        fitness = np.sum((synth_spectrum_flux -
                          self.observed_spectrum_flux) ** 2)

        return fitness, synth_spectrum


fitness_function_dict = {'simple_rms': SimpleRMSFitnessFunction}