import pytest

import hyperconf.errors as err

from hyperconf.dsl import ConfigDefs


@pytest.fixture(autouse=True)
def cleaup_before_test():
    ConfigDefs.clear()
    yield


def test_parse_one():
    defs = """
    test_def: int
    """
    assert ConfigDefs.parse_str(defs)


def test_parse_multiple():
    defs = """
    test_def:
     _type: str
     valid: asldkfj
    another_def:
      opt1: str
      opt2: str
    """
    types = ConfigDefs.parse_str(defs)
    assert len(types) == 2


def test_fail_invalid_option_type():
    defs = """
    test_def:
      valid_option: str
      another_valid_option:
        _type: int
        validator: '>3'
      invalid_option:
        - _type: int
        - validator: '<4'
    """
    with pytest.raises(err.TemplateDefinitionError):
        ConfigDefs.parse_str(defs)


def test_fail_when_nested():
    defs = """
    test_def:
      some_opt: str
      nested_def:
       another_opt: str
    """
    with pytest.raises(err.TemplateDefinitionError,
                       match=".*nesting.*not.*allowed.*"):
        ConfigDefs.parse_str(defs)


def test_reference_def():
    defs = """
    test_def:
      opt1: str
      opt2: int
    referencing_def:
      opt1: int
      opt2: test_def
    """
    ConfigDefs.parse_str(defs)


def test_parse_invalid_use():
    defs = """
    use:
     some_opt: str
     other_opt: int
    """
    with pytest.raises(err.TemplateDefinitionError,
                       match=".*must.*file.*path.*"):
        ConfigDefs.parse_str(defs)


def test_parse_use_not_found():
    defs = """
    use: invalid_path
    """
    with pytest.raises(err.TemplateDefinitionError,
                       match=".*Failed.*to.*load.*"):
        ConfigDefs.parse_str(defs)


def test_parse_valid_use():
    defs = """
    use: ./tests/defs
    """
    ConfigDefs.parse_str(defs)
    assert ConfigDefs.contains("ref1")
