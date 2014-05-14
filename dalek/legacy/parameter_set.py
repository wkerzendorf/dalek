from tardis import  analysis
from tardis.io import config_reader
import logging

import pandas as pd
import numpy as np
import copy
import yaml
import cPickle as pickle
from dalek.legacy import launcher
import os

logger = logging.getLogger(__name__)



def getitem_hierarchical(config_dict, hierarchy):
    if len(hierarchy) > 1:
        return getitem_hierarchical(config_dict[hierarchy[0]], hierarchy[1:])
    elif len(hierarchy) == 1:
        return config_dict[hierarchy[0]]
    else:
        raise KeyError('could not find %s' % hierarchy)

def setitem_hierarchical(config_dict, hierarchy, value):
    if len(hierarchy) > 1:
        return setitem_hierarchical(config_dict[hierarchy[0]], hierarchy[1:], value)
    elif len(hierarchy) == 1:
        config_dict[hierarchy[0]] = value
    else:
        raise KeyError('could not find %s' % hierarchy)

class DalekParameterSet(object):

    @classmethod
    def from_yaml(cls, yaml_fname):
        default_config_dict = yaml.load(open(yaml_fname))
        return cls(default_config_dict)

    @classmethod
    def from_hdf5(cls, h5_fname, parameter_set_name='dalek_group', default_configuration_name='config_dict'):
        hdf_store = pd.HDFStore(h5_fname)

        parameter_set_name = hdf_store[parameter_set_name]

        try:
            default_config_dict = pickle.loads(hdf_store[default_configuration_name].ix['config_dict'][0])
        except KeyError:
            default_config_dict = None
            logger.warn('default configuration dictionary not found in HDF5 file - suspected old version of DALEK h5')
        hdf_store.close()
        return cls(default_config_dict, parameter_set_name)




    def __init__(self, default_config_dict, parameter_sets=None):
        self.default_configuration = config_reader.TARDISConfigurationNameSpace(default_config_dict)
        self.parameter_sets = parameter_sets



    def add_parameter_iteration(self, parameter_name, parameter_values):
        parameter_hierarchy = parameter_name.split('.')
        try:
            getitem_hierarchical(self.default_configuration.config_dict, parameter_hierarchy)
        except KeyError:
            raise ValueError('Parameter %s not found in hierarchical_dict' % parameter_name)

        new_data_dict = {parameter_name:parameter_values, 'merge_key':np.ones_like(parameter_values, dtype=int)}
        if self.parameter_sets is None:
            self.parameter_sets = pd.DataFrame(new_data_dict)
        else:
            self.parameter_sets = pd.merge(self.parameter_sets, pd.DataFrame(new_data_dict), on='merge_key')

    def add_parameter(self, parameter_name, parameter_default=None):
        parameter_hierarchy = parameter_name.split('.')
        try:
            getitem_hierarchical(self.default_configuration.config_dict, parameter_hierarchy)
        except KeyError:
            raise ValueError('Parameter %s not found in hierarchical_dict' % parameter_name)

        self.parameter_sets[parameter_name] = parameter_default



    def generate_parameter_set_lists(self, generate_history_fnames=False):
        parameter_sets = []
        if generate_history_fnames:
            self.parameter_sets['history_fname'] = None
        for id, row in self.parameter_sets.iterrows():
            current_config = copy.deepcopy(self.default_configuration.config_dict)
            history_fname_list = ['history']
            for column in row.index:
                if column in ['merge_key', 'history_fname', 'history_objects', 'no_iterations']:
                    continue

                if column == 'plasma.nlte.species':
                    if not row[column]:
                        history_fname_list += ['species-%s' % row[column]]
                    else:
                        history_fname_list+= ['species-%s' % ('_'.join(row[column]),)]

                else:
                    history_fname_list += ['%s-%s' % (column.split('.')[-1], row[column])]
                if not row[column]:
                    continue

                setitem_hierarchical(current_config, column.split('.'), row[column])
            if generate_history_fnames:
                current_history_fname = '_'.join(history_fname_list) + '.h5'
                current_history_fname = current_history_fname.replace(' ', '.').replace('/', '_')
                self.parameter_sets['history_fname'][id] = current_history_fname
            parameter_sets.append(current_config)

        return parameter_sets

    def to_hdf5(self, h5_fname):
        hdf_store = pd.HDFStore(h5_fname)
        hdf_store['dalek_group'] = self.parameter_sets
        hdf_store['config_dict'] = pd.DataFrame([pickle.dumps(self.default_configuration.config_dict)],
                                                index=['config_dict'])
        hdf_store.close()

    def load_sets_history(self, history_dir):
        history_objects = []
        for idx, parameter_set in self.parameter_sets.iterrows():
            try:
                iterations = np.arange(1, parameter_set['no_iterations']+1)
            except KeyError:
                iterations = None
            history_fname = parameter_set['history_fname']
            logger.info('Reading %s', history_fname)
            history_objects.append(analysis.TARDISHistory(os.path.join(history_dir, history_fname), iterations=iterations))

        self.parameter_sets['history_objects'] = history_objects

    def launch_parameter_set(self, clients, history_dir=None):
        load_balanced_view = clients.load_balanced_view()
        if history_dir:
            print "generating history_fnames"
            parameter_collection = self.generate_parameter_set_lists(generate_history_fnames=True)
            history_fnames = [os.path.join(history_dir, item) for item in self.parameter_sets['history_fname']]
            print history_fnames[0]
            self.amr = load_balanced_view.map(launcher.dalek_worker, parameter_collection, history_fnames)
        else:
            parameter_collection = self.generate_parameter_set_lists(generate_history_fnames=False)
            self.amr = load_balanced_view.map(launcher.dalek_worker, parameter_collection)

        self.amr.wait_interactive()
        self.parameter_sets['no_iterations'] = self.amr.get()
