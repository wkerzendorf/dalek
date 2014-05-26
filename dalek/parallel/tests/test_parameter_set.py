import pytest
from dalek.parallel.parameter_collection import ParameterCollection, broadcast, merge_dicts, apply_dict
from tardis.io.config_reader import ConfigurationNameSpace

def test_simple_cartesian1():
    param1 = ParameterCollection({'a.b.param1' : [0.1, 0.2, 0.3]})
    param2 = ParameterCollection({'a.b.param2' : [0.1, 0.2, 0.3, 0.4]})
    assert len(param1) == 3
    assert len(param2) == 4
    combined = param1.cartesian_product(param2)
    assert len(combined) == 12


def test_add1():
    param1 = ParameterCollection({'a.b.param1' : [0.1, 0.2]})
    param2 = ParameterCollection({'a.b.param2' : [0.3, 0.4]})
    sum_ = param1.join(param2)
    assert len(sum_) == 2
    assert 'a.b.param1' in sum_
    assert 'a.b.param2' in sum_

@pytest.mark.skipif(True, reason='This does not work yet, need to think about'
                                 ' implementation')
def test_add2():
    param1 = ParameterCollection({'a.b.param1' : [0.5]})
    param2 = ParameterCollection({'a.b.param2' : [0.1, 0.2, 0.3]})
    sum_ = param1.join(param2)
    assert len(sum_) == 3
    assert {'a.b.param1' : 0.5, 'a.b.param2' : 0.1} in sum_.table
    assert {'a.b.param1' : 0.5, 'a.b.param2' : 0.2} in sum_.table
    assert {'a.b.param1' : 0.5, 'a.b.param2' : 0.3} in sum_.table

@pytest.mark.skipif(True, reason='This does not work yet, need to think about'
                                 ' implementation')
def test_add3():
    param1 = ParameterCollection({'a.b.param2' : [0.1, 0.2, 0.4, 0.5]})
    param2 = ParameterCollection({'a.b.param1' : [0.5, 1.0]})
    sum_ = param1 + param2
    assert len(sum_) == 4
    assert {'a.b.param1' : 0.5, 'a.b.param2' : 0.1} in sum_.table
    assert {'a.b.param1' : 1.0, 'a.b.param2' : 0.2} in sum_.table
    assert {'a.b.param1' : 0.5, 'a.b.param2' : 0.4} in sum_.table
    assert {'a.b.param1' : 1.0, 'a.b.param2' : 0.5} in sum_.table

@pytest.mark.skipif(True, reason='This does not work yet, need to think about'
                                 ' implementation')
def test_construct():
    param1 = ParameterCollection({'a.b.param1' : [0.0, 0.1], 'a.c.param2' : [0.1, 0.0]})
    param2 = ParameterCollection({'a.b.param1' : [0.5], 'a.c.param2' : [0.0, 0.1, 0.2]})
    param3 = ParameterCollection({})
    assert param1.table == [{'a.b.param1' : 0.0, 'a.c.param2' : 0.1}, {'a.b.param1' : 0.1, 'a.c.param2' : 0.0}]
    assert param2.table == [{'a.b.param1' : 0.5, 'a.c.param2' : 0.0}, {'a.b.param1' : 0.5, 'a.c.param2' : 0.1}, {'a.b.param1' : 0.5, 'a.c.param2' : 0.2}]
    assert param3.table == []

def test_to_config():
    config = ConfigurationNameSpace({'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4})
    param = ParameterCollection({'a' : [0.1, 0.2], 'c' : [0.3, 0.4]})
    new_configs = param.to_config(config)
    assert len(new_configs) == 2
    assert {'a' : 0.1, 'b' : 2, 'c' : 0.3, 'd' : 4} in new_configs
    assert {'a' : 0.2, 'b' : 2, 'c' : 0.4, 'd' : 4} in new_configs

def test_broadcast():
    assert broadcast([6.0], 3) == [6.0, 6.0, 6.0]
    assert broadcast([1, 2, 3], 9) == [1, 2, 3, 1, 2, 3, 1, 2, 3]
    assert broadcast([], 10) == []
    assert broadcast([1], 0) == [1]

def test_merge_dicts():
    assert merge_dicts({}, {}) == {}
    assert merge_dicts({'a' : 1}, {}) == {'a' : 1}
    assert merge_dicts({}, {'b' : 1}) == {'b' : 1}
    assert merge_dicts({'a' : 1, 'b' : 2}, {'c' : 3, 'd' : 4}) == {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}

def test_apply_dict():
    d1 = {'a' : {'b' : 3, 'c' : 4}, 'b' : {'e' : {'z' : 8, 'x' : 9}, 'f' : 15}}
    d2 = {'a.b' : 2, 'b.e.x' : 4, 'b.f' : 0}
    new_d = apply_dict(d1, d2)
    assert new_d == {'a' : {'b' : 2, 'c' : 4}, 'b' : {'e' : {'z' : 8, 'x' : 4}, 'f' : 0}}

def test_combine_parameter_sets():
    pass
