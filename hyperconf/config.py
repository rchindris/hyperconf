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
    def load_yaml(path: str | Path, strict: bool = True):
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
                config_values = yaml.load(tfile, Loader=dsl._LineInfoLoader)
            except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
                raise err.HyperConfError(
                    f"Failed to load file {path}. Cause: {repr(e)}"
                )
        print("FIE ", path)
        return HyperConfig(path.stem, config_values,
                           strict=strict,
                           line=0,
                           fname=path.as_posix())

    @staticmethod
    def load_str(text: str, strict: bool = True):
        """Load configuraiton from string."""
        if text is None:
            raise ValueError("text is None")

        # Load built-in types.
        dsl.ConfigDefs.parse_yaml("builtins.yaml")

        try:
            config_values = yaml.load(text, Loader=dsl._LineInfoLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            raise err.HyperConfError(
                f"Failed to parse YAML. Cause: {repr(e)}"
            )
        return HyperConfig(None, config_values, strict, None)

    def __init__(self, ident: str,
                 config_values: dict,
                 hdef: dsl.HyperDef = None,
                 strict: bool = True,
                 line: int = 0,
                 fname: str = None):
        """Parse and validate configuration objects."""
        if config_values is None or not isinstance(config_values, dict):
            raise ValueError("config_values must be a dict object.")

        if dsl.Keywords.line in config_values:
            # The loader adds a __line__: 1 for the top level node.
            self._line = config_values[dsl.Keywords.line]
            del config_values[dsl.Keywords.line]
        else:
            self._line = line

        self.name = ident
        self._strict = strict
        self._file = fname
        self._htype = hdef

        print("FILE ", self._file)
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
            ident, htype = dsl.HyperDef.infer_type(decl_name, val, hdef)
            if htype is None:
                raise err.UndefinedTagError(ident, self._line)

            htype.validate(val, self._line, self._file)

            if isinstance(val, dict):
                self.update({
                    ident: HyperConfig(ident, val, htype,
                                       strict=strict,
                                       line=self._line,
                                       fname=self._file)
                })
            elif isinstance(val, list):
                # Require that all list elements are dicts.
                if any(type(_) != dict for _ in val):
                    raise err.ConfigurationError(
                        "List options must contain elements of type list "
                        f"(in list for option {decl_name})",
                        line=self._line,
                        fname=self._file)

                vals = HyperConfig(ident, {},  htype,
                                   strict=strict,
                                   line=self._line,
                                   fname=self._file)

                for elem in val:
                    elem_id, elem_decl = next(iter(elem.items()))
                    vals.update({
                        elem_id: HyperConfig(elem_id, elem_decl,
                                             strict=strict,
                                             line=self._line,
                                             fname=self._file)
                    })
                self.update({
                    ident: vals
                })
            else:
                self.update({ident: val})

    def __getattr__(self, attr: str):
        """Return attribute value."""
        if attr is None:
            raise ValueError("attr is None")
        if attr not in self:
            raise AttributeError(
                f"Invalid configuration key '{attr}' for "
                f"configuraiton object {self._htype}"
            )
        return self[attr]

    def __delitem__(self, v):
        """Not supported, read-only."""
        raise NotImplementedError("HyperConfig is read-only")


if __name__ == "__main__":
    config = HyperConfig.load_yaml("test_config.yaml")
    
