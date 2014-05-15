import itertools
import operator
from functools import reduce
import pandas as pd


def broadcast(lst, length):
    """Extend a given list so it has the given length by repeating values in it.

    Arguments:
    ----------
    lst -- a list
    length -- an integer greater than len(lst)

    Return:
    -------
    A copy of lst with itself appended to the end as many times as is needed for it
    to have the given length.
    """
    if lst == []:
        return []
    if length < len(lst):
        return lst
    lst = lst * (length / len(lst) + 1)
    lst = lst[:length]
    return lst

def merge_dicts(d1, d2):
    """Combine two dictionaries similar to set union.
    
    Arguments:
    ----------
    d1 -- first dictionary
    d2 -- second dictionary
    
    Return:
    -------
    A new dictionary sharing keys and values with both d1 and d2
    """
    return dict(d1.items() + d2.items())

def apply_dict(d1, d2):
    """Use values in the second dictionary to replace values in the first
    dictionary if they share the same key.

    Arguments:
    ----------
    d1 -- dictionary to make a copy of and replace values in
    d2 -- dictionary values from which will be used
    
    Return:
    -------
    A copy of d1 with values that share keys with d2 replaced by those values in d2
    """
    d_new = dict(d1)
    for key in d2.keys():
        path = key.split('.')
        leaf = d_new
        for part in path[:-1]:
            leaf = leaf[part]
        leaf[path[-1]] = d2[key]
    return d_new

def combine_parameter_sets(table1, table2, combiner):
    """Create a new parameter set from two parameter sets via a combiner function.

    Arguments:
    ----------
    s1 -- first list of dictionaries
    s2 -- second list of dictionaries
    combiner -- a two argument function that takes two dictionary lists and returns a 
    dictionary list combined with combiner
    
    Return:
    -------
    A combination of s1 and s2 according to combiner function
    """
    combined = combiner(table1, table2)
    new_table = []
    for table in combined:
        new_table.append(reduce(merge_dicts, table))
    return new_table

def add_dictionary_lists(table1, table2):
    n1, n2 = len(table1), len(table2)
    if n1 > n2:
        table1, table2 = table2, table1
        n1, n2 = n2, n1
    table1 = broadcast(table1, n2)
    combiner = lambda s1, s2: zip(s1, s2)
    return combine_parameter_sets(table1, table2, combiner)    

def mul_dictionary_lists(table1, table2):
    combiner = lambda s1, s2: list(itertools.product(s1, s2))
    return combine_parameter_sets(table1, table2, combiner)    


class ParameterCollection2(pd.DataFrame):
    @property
    def _constructor(self):
        return ParameterCollection2

    def to_config_dict_list(self):
        pass


class ParameterCollection(object):
    """A set of parameters -- key/value pairs used for software configuration purposes.
    """
    def __init__(self, params):
        if params == {}:
            self.table = []
            return
        table = dict(params)
        # Let's make sure each value list is the same length by repeating the entries
        maximum = len(max(table.items(), key=lambda pair: len(pair[1]))[1])
        for key in table:
            length = len(table[key])
            if length < maximum:
                table[key] = broadcast(table[key], maximum)        
        items = table.items()
        zipped = zip(*[pair[1] for pair in items])
        labels = [table.keys()] * len(zipped)
        labeled = map(lambda pair: zip(*pair), zip(labels, zipped))
        self.table = [dict(pair) for pair in labeled]
        
    def to_config(self, config):
        """Apply parameter set to a configuration dictionary.

        Arguments:
        ----------
        config -- configuration dictionary
        
        Return:
        -------
        A list of dictionaries, each corresponding to a configuration dictionary
        with a parameter dictionary applied to it. There will be as many dictionaries
        as there are elements in the ParameterCollection.
        """
        new_configs = [apply_dict(config, param_set) for param_set in self]
        return new_configs

    def __add__(self, other):
        new_set = ParameterCollection({})
        new_set.table = add_dictionary_lists(self.table, other.table)
        return new_set

    def __mul__(self, other):
        new_set = ParameterCollection({})
        new_set.table = mul_dictionary_lists(self.table, other.table)
        return new_set

    def __getitem__(self, index):
        return self.table[index]

    def __len__(self):
        return len(self.table)

    def __str__(self):
        return str(self.table)
    
    def __repr__(self):
        return str(self.table)
    
