import dalek
from dalek.fitter import FitterConfiguration
import os

def get_test_data(fname):
    return os.path.join(dalek.__path__[0], 'fitter', 'tests', fname)

class TestYAMLRead():
    def setup(self):
        self.conf = FitterConfiguration.from_yaml(get_test_data('test_fitter_conf.yml'))
    
    def test_yaml_values(self):
        assert 0




def test_simple_fitter_configuration():
    #FitterConfiguration(['a.b', ])
    pass
