from tardis import config_reader
import pandas as pd
import numpy as np
import copy


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

class TARDISParameterSet(object):
    def __init__(self, default_yaml):
        self.default_configuration = config_reader.TARDISConfiguration.from_yaml(default_yaml)

        self.parameter_sets = None

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

    def add_column(self, parameter_name, parameter_default=None):
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
                if column == 'merge_key' or column == 'history_fname':
                    continue

                if column == 'plasma.nlte.species':
                    if not row[column]:
                        history_fname_list += ['species-%s' % row[column]]
                    else:
                        species_string_list = []
                        for species in row[column]:
                            species_string_list += [config_reader.species_tuple_to_string(species,
                                                                              self.default_configuration.atom_data).replace(' ', '')]
                        history_fname_list+= ['species-%s' % ('_'.join(species_string_list),)]

                else:
                    history_fname_list += ['%s-%s' % (column.split('.')[-1], row[column])]
                if not row[column]:
                    continue

                setitem_hierarchical(current_config, column.split('.'), row[column])
            if generate_history_fnames:
                self.parameter_sets['history_fname'][id] = '_'.join(history_fname_list) + '.h5'
            parameter_sets.append(current_config)

        return parameter_sets
