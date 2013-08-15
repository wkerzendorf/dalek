from tardis import config_reader, atomic
import os
import logging
from IPython.parallel.util import interactive

logger = logging.getLogger(__name__)


def set_engines_cpu_affinity():
    import sys
    if sys.platform.startswith('linux'):
        try:
            import psutil
        except ImportError:
            logger.warning('psutil not available - can not set CPU affinity')
        else:
            from multiprocessing import cpu_count
            p = psutil.Process(os.getpid())
            p.set_cpu_affinity(range(cpu_count()))


def prepare_remote_clients(clients, atom_data,  dalek_worker_dir):

    clients[:].execute('from tardis import config_reader, simulation, model_radial_oned')
    clients[:].execute('from astropy import units as u')
    clients[:].execute('import os')
    clients[:]['atom_data'] = atom_data
    clients[:]['dalek_worker_dir'] = dalek_worker_dir

    for client in clients:
        client.apply(set_engines_cpu_affinity)




@interactive
def dalek_worker(config_dict, history_fname=None):
    tardis_config = config_reader.TARDISConfiguration.from_config_dict(config_dict, atom_data=atom_data)

    if history_fname is not None:
        history_fname = os.path.join(dalek_worker_dir, history_fname)
    radial1d_mdl = model_radial_oned.Radial1DModel(tardis_config)
    simulation.run_radial1d(radial1d_mdl, history_fname)

    return radial1d_mdl.iterations_executed


def dalek_launcher(clients, parameter_sets, history_dir=None):
    load_balanced_view = clients.load_balanced_view()
    if history_dir:
        clients[:]['history_dir'] = [os.path.join(clients[:]['dalek_worker_dir'])]
        parameter_collection = parameter_sets.generate_parameter_set_lists(generate_history_fnames=True)
        #return parameter_collection
        history_fnames = [os.path.join(history_dir, item) for item in parameter_sets.parameter_sets['history_fname']]
        amr = load_balanced_view.map(dalek_worker, parameter_collection, history_fnames)
    else:
        parameter_collection = parameter_sets.generate_parameter_set_lists(generate_history_fnames=False)
        amr = load_balanced_view.map(dalek_worker, parameter_collection)

    return amr