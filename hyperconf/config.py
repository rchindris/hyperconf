"""Load and access configuration data."""
from collections import UserDict
from pathlib import Path

import yaml
from hyperconf.errors import HyperConfError, UndefinedTagError
from hyperconf.templates import ObjectTemplates
from hyperconf.yaml import LineInfoLoader


def load_yaml(path: str | Path = None,
              allow_undefined: bool = True):
    """Parse a YAML configuration file.

    :param config_path: path to a *YAML* file.
    :param strict: require that any YAML node is defined. Defaults to True.
    :return: a :class:`HyperConfig` instance.
    :type config_path: dict
    :type strict: bool
    :rtype: :class:`HyperConfig`
    :raises ValueError: when the path is None, not a str or Path.
    :raises IOError: when the file cannot be found.
    :raises HyperConfError: when the file is invalid.
    """
    if path is None or not isinstance(path, str) or not isinstance(path, Path):
        raise ValueError("Invalid value for 'path'. Please provide a valid "
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
    """Provide configuration values.

    A :class:`HyperConfig` instance is the result of parsing a dictionary
    containing configuration options, typically obtained through loading a
    YAML file by using the :func:`load_yaml` function.

    *Accesssing values*
    -------------------


    Configuration values can be of primitive types or can be nested. The
    configuration data can be acessed in two ways:

    - using dictionary syntax, with string keys::

        >> config = hyperconfig.config.load("test_config.yaml")
        >> config["database"]["hostname"]

    - using property syntax::

        >> config = hyperconfig.config.load("test_config.yaml")
        >> config.database.hostname

    Since :class:`HyperConfig` is a :class:`UserDict``, instances of it
    can be used like any Python dictionary. However, it is readonly, modifying
    configuration values is forbidded.

    *Templates, parsing and validation*
    -----------------------------------

    *hyperconf* is more than a simple YAML loader: it validates the
    configuration structure and values against a *configuration template*. A
    configuration template defines the required configuration nodes, the node
    contents and the data format for configuration options,
    see :mod:`hyperconf.templates` for details.

    The node template is available for each :class:`HyperConfig` instance
    through the *__meta__* property::

        >> config = hyperconfig.config.load("test_config.yaml")
        >> config.database.__meta__

    When a :class:`HyperConfig` is initialized in *strict* mode, each
    configuration object is required to have a template available and it is
    validated agains it's definition.
    """

    def __init__(self, config, templates,
                 definition=None, config_path=None, strict=True):
        """Instance initalization.

        :param config: map containing configuration keys and values.
        :type config: dict
        :param templates: object template definitions.
        :type templates:  :class:`ObjectTemplates`
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
                        f"'{decl_name}'. Cause {e}"
                    )
            else:
                # Argument
                arg_def = definition.get_arg(decl_name)
                arg_val = arg_def.type(decl)
                self.data[decl_name] = arg_val
                setattr(self, decl_name, arg_val)

    def __setitem__(self, key, item):
        """Not supported."""
        raise NotImplementedError("HyperConfig is readonly.")

    def __delitem__(self, key):
        """Not supported."""
        raise NotImplementedError("HyperConfig is readonly.")


if __name__ == "__main__":
    hc = load_yaml("test_config.yaml", allow_undefined=False)
    print(hc)
