import yaml
import pytest

from hyperconf import HyperConfig
from hyperconf import errors as err
from hyperconf.dsl import ConfigDefs


@pytest.fixture(autouse=True)
def cleaup_before_test():
    ConfigDefs.clear()
    yield

@pytest.fixture
def invalid_use_yaml():
    return """
    use: does_not_exist.yaml
    """

@pytest.fixture
def valid_yaml_builtin_types():
    return """
    use: tests/test_defs.yaml
    
    hello=str: "Hello!"
    halo=str: "Hallo!"
    ciao=str: "Ciao!"
    salut: "Salut!"
    year: 2023
    year=pos_int: 2023
    """

@pytest.fixture()
def valid_yaml_complex_defs():
    return """
    use: tests/test_defs.yaml

    model1=detector:
      stem: some_class_name
      heads:
        - head1:
            labels: labels1.json
        - head2:
            labels: labels2.json
    """

def test_invalid_use(invalid_use_yaml):
    with pytest.raises(err.TemplateDefinitionError):
        HyperConfig.load_str(invalid_use_yaml)


def test_valid_use(valid_yaml_builtin_types):
    HyperConfig.load_str(valid_yaml_builtin_types)
    assert ConfigDefs.contains("float")


def test_infer_explicit(valid_yaml_builtin_types):
    vals = HyperConfig.load_str(valid_yaml_builtin_types)
    assert ConfigDefs.contains("pos_int")
    assert vals.year == 2023


def test_infer_implicit(valid_yaml_builtin_types):
    vals = HyperConfig.load_str(valid_yaml_builtin_types)
    assert vals.salut and type(vals.salut) == str


def test_parse_simple_decl():
    defs = """
    use: tests/test_defs.yaml
    simple_str: hello world
    """
    config = HyperConfig.load_str(defs)
    assert "simple_str" in config and config.simple_str == "hello world"


def test_parse_complex_decl(valid_yaml_complex_defs):
    config = HyperConfig.load_str(valid_yaml_complex_defs)

    assert "model1" in config
    assert "head1" in config.model1.heads
    assert "head2" in config.model1.heads

def test_ships():
    defs = """
    use: tests/ships

    ncc1701=ship:
      captain: James T. Kirk
      crew: 156
      class: galaxy
      color: gray
      shields: 1.0
      engines: 900
    """
    config = HyperConfig.load_str(defs)
    print(config.ncc1701.captain)
