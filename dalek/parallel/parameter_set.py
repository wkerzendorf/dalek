import itertools

class ParameterSet(object):

    def __init__(self):
        self.table = {}
        
    def add_parameter(self, parameter, values, cartesian=False):
        """Add a new set of values for the given parameter.
        """
        self.table[parameter] = [values, cartesian]

    def to_config(default_config):
        for key, value in self.table:
            path = key.split('.')
    
    def __repr__(self):
        print self.table
    