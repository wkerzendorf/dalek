import dalek
from dalek.fitter import FitterConfiguration
import os

import numpy.testing as nptesting

def get_test_data(fname):
    return os.path.join(dalek.__path__[0], 'fitter', 'tests', fname)

class TestYAMLRead():
    def setup(self):
        self.conf = FitterConfiguration.from_yaml(get_test_data('test_fitter_conf.yml'))
    
    def test_yaml_values(self):
        assert self.conf.parameter_config.parameter_names[0] == 'param.b'
        nptesting.assert_allclose(self.conf.parameter_config.lbounds[0], -1)
        assert self.conf.atom_data is not None





def test_simple_fitter_configuration():
    #FitterConfiguration(['a.b', ])
    pass
