import math
from wbi import config


def test_str():
    assert config.test.string == "Hello"


def test_int():
    assert config.test.int == 42


def test_float():
    assert math.isclose(config.test.float, math.pi)


def test_none():
    assert config.test.none is None


def test_nested_bool():
    assert config.test.nested.bool is True


def test_nested_list():
    assert len(config.test.nested.list) == 4
    assert config.test.nested.list[2] == "Inky"
