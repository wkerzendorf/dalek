import pandas as pd
import h5py
import numpy as np
import pylab as plt
from matplotlib import animation
from specutils import Spectrum1D

from dalek.util import savitzky_golay

from collections import OrderedDict

from tardis.io.config_reader import ConfigurationNameSpace

from dalek import triangle


class Analyse(object):

    def __init__(self, fitter_log_fname, spectral_store_fname=None,
                 normalize_abundances=True):
        self.fitter_log = pd.read_csv(fitter_log_fname, index_col=0)

        self.spectral_store_fname = spectral_store_fname
        self.data_columns = [item for item in self.fitter_log.columns
                             if not item.startswith('dalek.')]
        self.abundance_columns = [item for item in self.data_columns
                             if 'abundance' in item]

        if normalize_abundances:
            self.fitter_log[self.abundance_columns] = (
                self.fitter_log[self.abundance_columns].values /
                self.fitter_log[self.abundance_columns].sum(axis=1).values[None].T)

        self.data_labels = []

        for column in self.data_columns:
            if column.endswith('item0'):
                label = '.'.join(column.split('.')[-2:])
            elif column in self.abundance_columns:
                label = column.split('.')[-1].lower().title()
            else:
                label = column.split('.')[-1]

            self.data_labels.append((column, label))
        self.data_labels = OrderedDict(self.data_labels)


    def visualize_parameter_evolution(self, parameter_name, bins=10, ax=None, **kwargs):
        """

        :param parameter_name:
        :return:
        """

        param_evolution_hist = np.empty((bins, len(
            self.fitter_log['dalek.current_iteration'].unique())))

        hist, bin_edges = np.histogram(self.fitter_log[parameter_name])

        for i in xrange(param_evolution_hist.shape[1]):
            data = self.fitter_log[parameter_name][
                self.fitter_log['dalek.current_iteration'] == i]
            hist, bin_edges = np.histogram(data, bins=bin_edges)
            param_evolution_hist[:,i] = hist

        if ax is None:
            ax = plt.gca()

        param_evolution_hist[param_evolution_hist == 0.0] = np.nan
        ax.imshow(param_evolution_hist, aspect='auto', extent=(
            param_evolution_hist.shape[0], param_evolution_hist.shape[-1],
            bin_edges[-1], bin_edges[0]), interpolation='nearest')


        ax.set_xlabel('Iterations')
        ax.set_ylabel(self.data_labels[parameter_name])

        return param_evolution_hist

    def visualize_triangle_plot(self, truth_config=None, plot_contours=False, bins=100):
        if truth_config is not None:
            truth_config = ConfigurationNameSpace.from_yaml(truth_config)

        fitness = self.fitter_log['dalek.fitness']
        truths = []
        for column in self.data_columns:

            if truth_config is not None:
                default_value = truth_config.get_config_item(column)
                default_value = getattr(default_value, 'value', default_value)
                truths.append(default_value)

        if truths == []:
            truths = None



        triangle.corner(self.fitter_log[self.data_columns], weights=1/fitness,
                        labels=self.data_labels.values(), plot_contours=plot_contours,
                        normed=True, truths=truths, bins=bins)

    def animate_fitting_evolution(self, fit_spectrum, spectral_store, mode='best', movie_fname=None):

        fit_wave, fit_flux = np.loadtxt(fit_spectrum, unpack=True)
        fit_flux = savitzky_golay(fit_flux, 21, 3)
        iterations = self.fitter_log['dalek.current_iteration'].unique()
        fh = h5py.File(spectral_store, 'r')
        fluxes = []
        for i in iterations:
            if mode == 'best':
                spec_idx = (self.fitter_log[
                                self.fitter_log['dalek.current_iteration'] == i]
                            ['dalek.fitness'].argmin())
            fluxes.append(savitzky_golay(np.array(fh['spectral_store/'
                                      'spectrum{0}'.format(spec_idx)]), 21, 3))

        fluxes = np.array(fluxes)

        fh.close()

        # First set up the figure, the axis, and the plot element we want to animate
        fig = plt.figure(facecolor='black')
        ax = plt.axes(xlim=(2000, 10000), ylim=(0, 1.2e-13))
        ax.set_xticks(np.arange(2000, 10000, 3000))
        ax.set_axis_bgcolor('black')
        ax.plot(fit_wave, fit_flux, lw=2, color='red')
        line, = ax.plot([], [], lw=2, alpha=.8, color='yellow')
        txt = ax.text(0.7, 0.8,'', horizontalalignment='center',
                          verticalalignment='center', transform=ax.transAxes)
        # initialization function: plot the background of each frame
        def init():
            line.set_data([], [])
            return line,

        # animation function.  This is called sequentially
        def animate(i):
            line.set_data(fit_wave, fluxes[i])
            txt.set_text('iteration {0:03d}'.format(i))
            return line,

        # call the animator.  blit=True means only re-draw the parts that have changed.
        anim = animation.FuncAnimation(fig, animate, init_func=init,
                                       frames=len(iterations), interval=100,
                                       blit=False)

        # save the animation as an mp4.  This requires ffmpeg or mencoder to be
        # installed.  The extra_args ensure that the x264 codec is used, so that
        # the video can be embedded in html5.  You may need to adjust this for
        # your system: for more information, see
        # http://matplotlib.sourceforge.net/api/animation_api.html
        if movie_fname is not None:
            anim.save(movie_fname, fps=30, extra_args=['-vcodec', 'libx264',
                                                       '-pix_fmt', 'yuv420p'],
                      savefig_kwargs={'facecolor':'black'})
        return anim