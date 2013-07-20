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

    def __iter__(self):
        self.current_parameter_set_id = -1
        return self

    def next(self):
        current_config = copy.deepcopy(self.default_configuration.config_dict)
        self.current_parameter_set_id += 1
        if self.current_parameter_set_id >= len(self.parameter_sets):
            raise StopIteration

        current_parameter_set = self.parameter_sets.iloc[self.current_parameter_set_id]
        for column in current_parameter_set.keys():
            if column == 'merge_key':
                continue
            setitem_hierarchical(current_config, column.split('.'), current_parameter_set[column])
        return current_config
