import os

import dalek
from dalek.priors.base import GaussianPrior
import numpy.testing as npt
import numpy as np
import pytest


@pytest.fixture
def yaml_fname():
    return os.path.join(dalek.__path__[0], 'priors', 'tests', 'data',
                        'prior_test.yml')

def test_gaussian():
    gp = GaussianPrior(0, 1)
    assert np.isclose(gp(0.5), 0.0)

def test_yaml_reader(yaml_fname):
    1 / 0