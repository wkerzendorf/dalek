from dalek.priors.base import GaussianPrior
import numpy.testing as npt
import numpy as np


def test_gaussian():
    gp = GaussianPrior(0, 1)
    assert np.isclose(gp(0.5), 0.0)
