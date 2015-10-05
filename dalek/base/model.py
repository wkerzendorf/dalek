import copy

from tardis.io.config_reader import ConfigurationNameSpace, Configuration
from tardis import run_tardis, model, simulation, atomic
from astropy import units as u, constants as const

from astropy.modeling import Model, Parameter
import numpy as np
from collections import OrderedDict

def intensity_black_body_wavelength(wavelength, T):
    wavelength = u.Quantity(wavelength, u.angstrom)
    T = u.Quantity(T, u.K)
    pref = ((8 * np.pi * const.h * const.c) / wavelength**5)
    return pref / (np.exp((const.h * const.c)/(wavelength * const.k_B * T)) - 1)


class TARDISModelMixin(Model):
    inputs = tuple()
    outputs = ('packet_nu', 'packet_energy', 'virtual_nu', 'virtual_energy',
               'param_name', 'param_value')

    def __init__(self, config_name_space, **kwargs):
        self.config_name_space = config_name_space
        self.atom_data = atomic.AtomData.from_hdf5(config_name_space.atom_data)
        super(TARDISModelMixin, self).__init__(**kwargs)

    def evaluate(self, *args, **kwargs):
        config_name_space = copy.deepcopy(self.config_name_space)
        for i, param_value in enumerate(args):
            config_name_space.set_config_item(
                self.convert_param_dict.values()[i], param_value)
        config = Configuration.from_config_dict(config_name_space,
                                                validate=False,
                                                atom_data=self.atom_data)
        radial1d_mdl = model.Radial1DModel(config)
        simulation.run_radial1d(radial1d_mdl)
        runner = radial1d_mdl.runner

        param_names = ['t_inner']
        param_values = [radial1d_mdl.t_inner]
        return (runner.emitted_packet_nu,
                runner.emitted_packet_luminosity,
                runner.virt_packet_nus * u.Hz,
                (runner.virt_packet_energies /
                 runner.time_of_simulation),
                param_names, param_values)

class SimpleTARDISUncertaintyModel(Model):
    inputs = ('packet_nu', 'packet_energy', 'virtual_nu', 'virtual_energy',
              'param_names', 'param_values')
    outputs = ('wavelength', 'luminosity', 'uncertainty', 'param_names', 'param_values')


    def __init__(self, observed_wavelength, mode='virtual',
                 virtual_uncertainty_scaling=5.):
        self.observed_wavelength = observed_wavelength
        self.wavelength_bins = self._generate_bins(observed_wavelength)
        self.mode = mode
        self.virtual_uncertainty_scaling = virtual_uncertainty_scaling
        super(SimpleTARDISUncertaintyModel, self).__init__()

    @staticmethod
    def _generate_bins(observed_wavelength):
        hdiff = 0.5 * np.diff(observed_wavelength)
        hdiff = np.hstack((-hdiff[0], hdiff, hdiff[-1]))
        bins = np.hstack((observed_wavelength[0], observed_wavelength)) + hdiff
        return bins

    def evaluate(self, packet_nu, packet_energy, virtual_nu, virtual_energy,
                 param_names, param_values):
        packet_lambda = packet_nu.to(u.angstrom, u.spectral())
        bin_counts = np.histogram(packet_lambda, bins=self.wavelength_bins)[0]

        uncertainty = (np.sqrt(bin_counts) * np.mean(packet_energy)
                       / np.diff(self.wavelength_bins))

        if self.mode == 'normal':
            luminosity = np.histogram(packet_lambda,
                          weights=packet_energy,
                          bins=self.wavelength_bins)[0]
        elif self.mode == 'virtual':
            virtual_packet_lambda = virtual_nu.to(u.angstrom, u.spectral())
            luminosity = np.histogram(virtual_packet_lambda,
                          weights=virtual_energy,
                          bins=self.wavelength_bins)[0]
            uncertainty /= self.virtual_uncertainty_scaling

        luminosity_density = luminosity / np.diff(self.wavelength_bins)


        return (self.observed_wavelength, luminosity_density, uncertainty.value,
                param_names, param_values)



class NormRedSpectrum(Model):
    inputs = ('wavelength', 'flux', 'uncertainty', 'param_names', 'param_values')
    outputs = ('wavelength', 'flux', 'uncertainty', 'param_names', 'param_values')

    def __init__(self, norm_start=6300):
        super(NormRedSpectrum, self).__init__()
        self.norm_start = 6300

    def evaluate(self, wavelength, flux, uncertainty, param_names, param_values):
        param_dict = OrderedDict(zip(param_names, param_values))

        norm_start_idx = wavelength.searchsorted(self.norm_start)
        norm_curve = intensity_black_body_wavelength(
            wavelength[norm_start_idx:], param_dict['t_inner'])
        norm_curve /= norm_curve[0]

        normed_flux = flux.copy()
        normed_flux[norm_start_idx:] *= norm_curve
        normed_uncertainty = uncertainty.copy()
        normed_uncertainty[norm_start_idx:] *= norm_curve
        return (wavelength, normed_flux, normed_uncertainty,
                param_names, param_values)




class LogLikelihood(Model):
    inputs = ('wavelength', 'flux', 'uncertainty', 'param_names',
              'param_values')
    outputs = ('loglikelihood',)

    def __init__(self, observed_wavelength, observed_flux,
                 observed_uncertainty):
        self.observed_wavelength = observed_wavelength
        self.observed_flux = observed_flux
        self.observed_uncertainty = observed_uncertainty
        super(LogLikelihood, self).__init__()

    def evaluate(self, wavelength, flux, uncertainty, param_names,
                 param_values):
        return (-0.5 * np.sum((self.observed_flux - flux)**2 /
                              (uncertainty**2 + self.observed_uncertainty**2)))


def _convert_param_names(param_names):
    """

    :param param_names:
    :return:
    """
    short_param_names = []
    for param_name in param_names:
        if param_name.split('.')[-1].startswith('item'):
            short_param_name = "{0}_{1}".format(
                param_name.split('.')[-2],
                param_name.split('.')[-1].replace('item', ''))
        else:
            short_param_name = param_name.split('.')[-1]


    short_param_names = [item.split('.')[-1] for item in param_names]
    if len(set(short_param_names)) != len(param_names):
        raise ValueError('Paramnames are not unique')

    return OrderedDict(zip(short_param_names, param_names))

def assemble_tardis_model(fname, param_names):
    """

    :param yaml_fname:
    :param param_names:
    :return:
    """

    config = ConfigurationNameSpace.from_yaml(fname)
    class_dict = {}
    param_dict = {}
    short_param_name_dict = _convert_param_names(param_names)

    class_dict['convert_param_dict'] = short_param_name_dict
    for key in short_param_name_dict:
        try:
            value = config.get_config_item(short_param_name_dict[key])
        except KeyError:
            raise ValueError('{0} is not a valid parameter'.format(key))
        else:
            pass
        class_dict[key] = Parameter()
        param_dict[key] = getattr(value, 'value', value)

    class_dict['__init__'] = TARDISModelMixin.__init__

    simple_model = type('SimpleTARDISModel', (TARDISModelMixin, ),
                        class_dict)
    return simple_model(config, **param_dict)

