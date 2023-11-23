"""Load and access configuration data."""
import yaml
from pathlib import Path

import hyperconf.errors as err
import hyperconf.dsl as dsl


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

        # Load built-in types.
        dsl.ConfigDefs.parse_yaml("builtins.yaml")

        if not path.exists() or not path.is_file():
            raise IOError(
                f"Could not load the configuration from {path}. "
                "Please check that the file exists."
            )

        with open(path) as tfile:
            try:
                config_values = yaml.load(tfile, Loader=dsl.LineInfoLoader)
            except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
                raise err.HyperConfError(
                    f"Failed to load file {path}. Cause: {repr(e)}"
                )
        return HyperConfig(config_values, strict, path)

    @staticmethod
    def load_str(text: str, strict: bool = True):
        """Load configuraiton from string."""
        if text is None:
            raise ValueError("text is None")

        try:
            config_values = yaml.load(text, Loader=dsl._LineInfoLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            raise err.HyperConfError(
                f"Failed to parse YAML. Cause: {repr(e)}"
            )
        return HyperConfig(config_values, strict, None)

    def __init__(self, config_values: dict,
                 strict: bool = True,
                 line: int = 0,
                 fname: str = None):
        """Parse and validate configuration objects."""
        if config_values is None or not isinstance(config_values, dict):
            raise ValueError("config_values must be a dict object.")

        if "__line__" in config_values:
            # The loader adds a __line__: 1 for the top level node.
            del config_values["__line__"]

        self._strict = strict
        self._file = fname
        self._line = line

        # Scan the entire file for use directives and
        # load referred definitions.
        objs = []
        for decl_name, val in config_values.items():
            if decl_name == dsl.Keywords.use:
                dsl.ConfigDefs.parse_yaml(val, 0, fname)
            else:
                objs.append((decl_name, val))

        # Parse objects
        for decl_name, val in objs:
            line = val.get(dsl.Keywords.line, -1) if\
                isinstance(val, dict) else -1

            ident, htype = dsl.infer_type(decl_name)
            if htype is None:
                raise err.UndefinedTagError(ident, line)

            htype.validate(val)

            if isinstance(val, dict):
                self.update({ident: HyperConfig(val, strict, fname)})
            elif isinstance(val, list):
                self.update({ident: [
                    HyperConfig(_, strict, fname) for _ in val
                ]})
            else:
                self.update({ident: val})

    def __getattr__(self, attr: str):
        """Return attribute value."""
        if attr is None:
            raise ValueError("attr is None")
        if attr not in self:
            raise AttributeError(attr)
        return self[attr]

    def __delitem__(self, v):
        """Not supported, read-only."""
        raise NotImplementedError("HyperConfig is read-only")


if __name__ == "__main__":
    config = HyperConfig.load_yaml("test_config.yaml")
    print(config.model.head[0].labels)
