from tardis import config_reader, atomic
import os

def prepare_remote_clients(clients, atom_data):
    clients[:]['atom_data'] = atom_data
    clients[:].execute('from tardis import config_reader, simulation, atomic')

def dalek_worker(config_dict, atom_data_fname, history_fname=None):
    import tardis.atomic as atomic
    import tardis.model_radial_oned as model_radial_oned
    import tardis.simulation as simulation
    import os
    import psutil
    from multiprocessing import cpu_count

    p = psutil.Process(os.getpid())
    p.set_cpu_affinity(range(cpu_count()))
    atom_data = atomic.AtomData.from_hdf5(atom_data_fname)
    tardis_config = config_reader.TARDISConfiguration(config_dict, atom_data)

    radial1d_mdl = model_radial_oned.Radial1DModel(tardis_config)
    simulation.run_radial1d(radial1d_mdl, history_fname)

    return radial1d_mdl.iterations_executed


def dalek_launcher(load_balanced_view, parameter_sets, atom_data_fname, history_dir=None):
    if history_dir:
        parameter_collection = parameter_sets.generate_parameter_set_lists(generate_history_fnames=True)
        history_fnames = [os.path.join(history_dir, item) for item in parameter_sets.parameter_sets['history_fname']]
        amr = load_balanced_view.map(dalek_worker, parameter_collection, [atom_data_fname]*len(parameter_collection),
                                     history_fnames)
    else:
        parameter_collection = parameter_sets.generate_parameter_set_lists(generate_history_fnames=False)
        amr = load_balanced_view.map(dalek_worker, parameter_collection, [atom_data_fname]*len(parameter_collection))

    return amr