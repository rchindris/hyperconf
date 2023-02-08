"""Provide configuration loading utilities."""
from collections import UserDict
from pathlib import Path


import yaml

from hyperconf.yaml import LineInfoLoader
from hyperconf.errors import HyperConfError, UndefinedTagError
from hyperconf.templates import ObjectTemplates


def load(path: str | Path = None,
         allow_undefined: bool = True):
    """Parse a YAML configuration file.

    Arguments:
    config_path (Dict): a dictionary containing configuration keys and
        values. May be a result of parsing a YAML file.
    strict (bool): if True, require that any configuration key has
        a definition in one of the referenced template files. Default: True.
    """
    if path is None:
        raise ValueError("path is None. Please provide a valid "
                         "string or Path object.")
    if isinstance(path, str):
        path = Path(path)

    if not path.exists() or not path.is_file():
        raise IOError(
            f"Could not load the configuration from {path}. "
            "Please check that the file exists."
        )

    with open(path) as tfile:
        try:
            config_yaml = yaml.load(tfile, Loader=LineInfoLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            raise HyperConfError(
                f"Failed to load file {path}. Cause: {repr(e)}"
            )

    if "__line__" in config_yaml:
        # The loader adds a __line__: 1 for the top level node.
        del config_yaml["__line__"]

    try:
        templates = ObjectTemplates.resolve(config_yaml)
        return HyperConfig(
            config_yaml,
            templates,
            config_path=path.as_posix(),
            strict=not allow_undefined
        )
    except HyperConfError as e:
        raise HyperConfError(
            f"Failed to load configuration from '{path}': {str(e)}"
        )


class HyperConfig(UserDict):
    """An object containing configuration."""

    def __init__(self, config, templates,
                 definition=None, config_path=None, strict=True):
        """Initialize a HyperConfig object from a dictionary.

        Arguments:
        config (dict): a dictionary containing object declarations.
        templates (ObjectTemplates): templates for the nodes in this config.
        definition (ObjectTemplates): the definition for this configuration object.
        config_path (str): configuration file path.
        strict (bool): when True, require that every node is defined.
        Default: True.
        """
        self.data = {}

        if "__line__" in config:
            decl_line = config["__line__"]
            del config["__line__"]
        else:
            decl_line = -1

        if definition:
            for opt in definition.get_args():
                if opt.name not in config:
                    # Required option is missing.
                    raise HyperConfError(
                        f"Missing required option '{opt.name}' for "
                        f"configuration object '{definition.name}'.",
                        decl_line,
                        config_path
                    )

        for decl_name, decl in config.items():
            if isinstance(decl, dict):
                # Nested configuration object.
                node_def = templates.get(decl_name, None)
                if node_def:
                    node_def.parse(decl)
                else:
                    if strict:
                        raise UndefinedTagError(
                            decl_name,
                            decl_line,
                            config_path
                        )
                try:
                    nested_obj = HyperConfig(
                        decl, templates, node_def,
                        config_path, strict
                    )
                    nested_obj["__def__"] = node_def

                    self.data[decl_name] = nested_obj
                    setattr(self, decl_name, nested_obj)
                except Exception as e:
                    raise HyperConfError(
                        f"Error while parsing node "
                        f"'{decl_name}'. Cause: {e}"
                    )
            else:
                # Argument
                arg_def = definition.get_arg(decl_name)
                arg_val = arg_def.type(decl)
                self.data[decl_name] = arg_val
                setattr(self, decl_name, arg_val)


if __name__ == "__main__":
    hc = load("test_config.yaml", allow_undefined=False)
    print(hc.model)
