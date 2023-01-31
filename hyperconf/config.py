"""Provide configuration loading utilities."""
import yaml

from collections import UserDict

from typing import Dict
from pathlib import Path

from hyperconf.yaml import LineInfoLoader
from hyperconf.errors import (
    InvalidYamlError,
    UndefinedTagError
)
from hyperconf.templates import NodeDefs


class HyperConfig(UserDict):
    """An object containing configuration. """

    def __init__(self, raw_config: Dict,
                 config_path: str = None,
                 strict: bool = True):
        """Initialize a HyperConfig object from a dictionary.

        Arguments:
        raw_config (Dict): a dictionary containing configuration keys and
        values. May be a result of parsing a YAML file.
        strict (bool): if True, require that any configuration key has
        a definition in one of the referenced template files. Default: True.
        """
        if raw_config is None:
            raise ValueError("raw_config is None")
        if not isinstance(raw_config, dict):
            raise ValueError("raw_config must be a dictionary")

        self._defs = NodeDefs()

        # Load all template references.
        if NodeDefs.Predefined.USE in raw_config:
            use_decl = raw_config[NodeDefs.Predefined.USE]
            use_def = self._defs[NodeDefs.Predefined.USE]
            use_val = use_def.parse(use_decl)
            self._defs.parse(use_val)
            del raw_config[NodeDefs.Predefined.USE]

        for decl_name, decl in raw_config.items():
            node_def = self._defs.get(decl_name, None)
            decl_line = decl["__line__"] if "__line__" in decl else None

            if node_def is None and strict:
                raise UndefinedTagErrror(decl_name,
                                         decl_line,
                                         config_path)

            try:
                self.data[decl_name] = node_def.parse(decl)
            except ...:
                # TODO proper error handling
                if strict:
                    raise InvalidYamlError(decl_name)


def load(path: str | Path, allow_undefined: bool = False):
    """Load configuration from a file.

    This function loads a YAML configuration file, resolves all referenced
    hyperconf definition files and returns the validated configuration
    object(s).
    The 'allow_undefined' parameter controls the strictness of the validation
    process: if False, any node found in the configuration file is required
    to be defined in a definition file.

    Arguments:
        path (str | Path): the path to the configuration file.
        allow_undefined (bool): return undefined nodes. Default: False.
    """
    if path is None:
        raise ValueError("path is None. Please provide a valid "
                         "string or Path object.")
    if isinstance(path, str):
        path = Path(path)

    if not path.exists() or not path.is_file():
        raise IOError(
            f"Could not load the configuration from {path}. "
            "Please check that the file exists.")

    with open(path) as tfile:
        try:
            config_yaml = yaml.load(tfile, Loader=LineInfoLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            raise InvalidYamlError(path.as_posix(), e)

    return HyperConfig(config_yaml, strict=not allow_undefined)


if __name__=="__main__":
    print(load("test_config.yaml"))
