from abc import ABCMeta, abstractmethod
import numpy as np
from specutils import Spectrum1D
from astropy import units as u, constants as const

class BaseFitnessFunction(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def get_spectrum(self, spectrum):
        """
        Function to make a spectrum out of a filename
        :param spectrum:
        :return:
        """


class SimpleRMSFitnessFunction(BaseFitnessFunction):

    def __init__(self, spectrum):

        if hasattr(spectrum, '.flux'):
            self.observed_spectrum = spectrum
        else:
            wave, flux = np.loadtxt(spectrum, unpack=True)
            self.observed_spectrum = Spectrum1D.from_array(wave * u.angstrom,
                                                           flux * u.erg / u.s /
                                                           u.cm**2 / u.Angstrom)


        self.observed_spectrum_wavelength = self.observed_spectrum.wavelength.value
        self.observed_spectrum_flux = self.observed_spectrum.flux.value

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