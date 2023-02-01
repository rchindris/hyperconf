"""Provide configuration loading utilities."""
import yaml

from collections import UserDict

from pathlib import Path
from typing import Dict

from hyperconf.yaml import LineInfoLoader
from hyperconf.errors import (
    InvalidYamlError,
    UndefinedTagError
)

from hyperconf.templates import NodeTemplates


class HyperConfig(UserDict):
    """An object containing configuration. """

    def __init__(self, config_path: str | Path = None,
                 allow_undefined: bool = True):
        """Initialize a HyperConfig object from a dictionary.

        Arguments:
        raw_config (Dict): a dictionary containing configuration keys and
        values. May be a result of parsing a YAML file.
        strict (bool): if True, require that any configuration key has
        a definition in one of the referenced template files. Default: True.
        """
        config = self._read_yaml(config_path)

        self._templates = NodeTemplates()
        self._templates.load_uses(config)

        for decl_name, decl in config.items():
            print(decl_name, decl)
            node_def = self._templates.get(decl_name, None)
            decl_line = decl["__line__"] if "__line__" in decl else None

            if node_def is None and allow_undefined:
                raise UndefinedTagErrror(decl_name,
                                         decl_line,
                                         config_path)
            try:
                self.data[decl_name] = node_def.parse(decl)
            except ...:
                # TODO proper error handling
                if allow_undefined:
                    raise InvalidYamlError(decl_name)

    def _read_yaml(self, path: str | Path):
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

        return config_yaml

if __name__=="__main__":
    hc = HyperConfig("test_config.yaml")
