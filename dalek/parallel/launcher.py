from tardis import run_tardis
import os
import logging

from IPython.parallel.util import interactive
logger = logging.getLogger(__name__)



def prepare_remote_clients(clients, atom_data):

    clients[:].execute('from tardis import config_reader, simulation, model_radial_oned')
    clients[:].execute('from astropy import units as u')
    clients[:].execute('import os')
    clients[:]['atom_data'] = atom_data

    for client in clients:
        client.apply(set_engines_cpu_affinity)






def dalek_launcher(clients, parameter_sets, history_dir=None):
    load_balanced_view = clients.load_balanced_view()
    if history_dir:

        parameter_collection = parameter_sets.generate_parameter_set_lists(generate_history_fnames=True)
        #return parameter_collection
        history_fnames = [os.path.join(history_dir, item) for item in parameter_sets.parameter_sets['history_fname']]
        amr = load_balanced_view.map(dalek_worker, parameter_collection, history_fnames)
    else:
        parameter_collection = parameter_sets.generate_parameter_set_lists(generate_history_fnames=False)
        amr = load_balanced_view.map(dalek_worker, parameter_collection)

    return amr


@interactive
def simple_worker(config_dict, atom_data=None):
    """
    This is a simple TARDIS worker that will run TARDIS and return the model

    Parameters
    ----------
    
    
    """


@interactive
def dalek_worker(config_dict,):
    tardis_config = config_reader.TARDISConfiguration.from_config_dict(config_dict, atom_data=atom_data)
    radial1d_mdl = model_radial_oned.Radial1DModel(tardis_config)
    simulation.run_radial1d(radial1d_mdl, history_fname)

    return radial1d_mdl

class BaseLauncher(object):

    def __init__(self, remote_clients, default_config, worker, atom_data=None):
        self.default_config = default_config
        
        self.prepare_remote_clients(remote_clients, atom_data)
        
    @staticmethod
    def prepare_remote_clients(clients, atom_data):

        clients[:].execute('from tardis import run_tardis')
        
        if atom_data is not None:
            clients[:]['atom_data'] = atom_data

    for client in clients:
        client.apply(set_engines_cpu_affinity)

    def __call__(self, config_update):
        return Async Result

    def add_to_queue(self, config_update):
        {'model.structure.abundances':{'Ca':0.5}}
        self.default_config.copy()
    
    def add_abundance_change_to_queue(self, {'ca':0.3, 'c':0.2})
    def add_paramset_to_queue(paramset):
        return list(async_objects)

    @staticmethod


