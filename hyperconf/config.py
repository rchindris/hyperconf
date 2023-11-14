"""Load and access configuration data."""
from pathlib import Path

import yaml
import hyperconf.errors as err
import hyperconf.dsl as dsl
from hyperconf.yaml import LineInfoLoader


class HyperConfig(dict):
    """Configuration file parser.

    This class provides schema validation by using configuration template
    definitions and configuration value validation.
    Accessing values can be done in a dict-like manner on by acessing
    attributes. All top-level configuration keys are exposed as attributes.
    """

    @staticmethod
    def load_yaml(path: str | Path = None, strict: bool = True):
        """Load configuration values from a YAML file."""
        if path is None or (not isinstance(path, str) and
                            not isinstance(path, Path)):
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
                config_values = yaml.load(tfile, Loader=LineInfoLoader)
            except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
                raise err.HyperConfError(
                    f"Failed to load file {path}. Cause: {repr(e)}"
                )
        return HyperConfig(config_values, strict, path)

    def __init__(self, config_values: dict,
                 strict: bool = True,
                 fname: str = None):
        """Parse and validate configuration objects."""
        if config_values is None or not isinstance(config_values, dict):
            raise ValueError("config_values must be a dict object.")

        if "__line__" in config_values:
            # The loader adds a __line__: 1 for the top level node.
            del config_values["__line__"]

        # Scan the entire file for use directives and
        # load any object definitions before parsing objects.
        objs = []
        for decl_name, val in config_values.items():
            if decl_name == dsl.Keywords.use:
                dsl.ConfigDefs.parse_yaml(val, 0, fname)
            else:
                objs.append((decl_name, val))

        # Parse objects
        for decl_name, val in objs:
            line = val.get(dsl.Keywords.line, -1) if isinstance(val, dict) else -1

            ident, hdef = dsl.infer_type(decl_name)
            if strict:
                if hdef is None:
                    raise err.UndefinedTagError(decl_name, line, fname)
                hdef.validate(val)

            if isinstance(val, dict):
                self.update({ident: HyperConfig(val, strict, fname)})
            else:
                self.update({ident: val})

    def __getattr__(self, attr: str):
        """Return attribute value."""
        if attr is None:
            raise ValueError("attr is None")
        if attr not in self:
            raise AttributeError(attr)
        return self[attr]

    def __setitem__(self, k, v):
        raise NotImplementedError("HyperConfig is read-only")

    def __delitem__(self, v):
        raise NotImplementedError("HyperConfig is read-only")


if __name__ == "__main__":
    config = HyperConfig.load_yaml("test_config.yaml")
