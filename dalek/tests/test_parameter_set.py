from dalek.parallel.parameter_set import ParameterSet

def test_simple_cartesian1():
    param1 = ParameterSet({'a.b.param1' : [0.1, 0.2, 0.3]})
    param2 = ParameterSet({'a.b.param2' : [0.1, 0.2, 0.3, 0.4]})
    combined = param1 * param2
    assert len(combined) == 12
