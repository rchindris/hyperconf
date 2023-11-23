import yaml
import pytest

from hyperconf import HyperConfig
from hyperconf.dsl import ConfigDefs


@pytest.fixture(autouse=True)
def cleaup_before_test():
    ConfigDefs.clear()
    yield


def test_use_directive():
    defs = """
    use: tests/test_defs.yaml
    """
    config = HyperConfig.load_str(defs)
    assert config is not None and ConfigDefs.contains("simple_str")


def test_parse_simple_decl():
    defs = """
    use: tests/test_defs.yaml
    simple_str: 'hello world'
    """
    config = HyperConfig.load_str(defs)
    assert "simple_str" in config and config.simple_str == "hello world"


def test_parse_complex_decl():
    pass
