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
    def load_yaml(path: str | Path, strict: bool = True) -> "HyperConfig":
        """Parse a YAML file containing configuration objects.

        :param path: The path to the YAML file. It can be either a string or
        a Path object.
        :type path: Union[str, Path]

        :param strict: If True, strict parsing is enforced. Defaults to True.
        :type strict: bool, optional

        :return: An instance of HyperConfig containing the parsed configuration
        :rtype: HyperConfig

        :raises FileNotFoundError: If the specified YAML file is not found.
        :raises HyperConfigError: If there are issues with
        parsing or validation.

        :Example:

        >>> config_path = 'path/to/config.yaml'
        >>> config = HyperConfig.load_yaml(config_path)
        >>> print(config.some_key)
        'some_value'

        :Example with non-strict parsing:

        >>> config_path = 'path/to/config.yaml'
        >>> config = HyperConfig.load_yaml(config_path, strict=False)
        >>> print(config.some_key)
        'some_value'

        :note:
            - If `strict` is set to True (default), the parser enforces strict
             validation meaning that each object has to have a type so that the
             object structure is validated.
            - If `strict` is set to False, the parser allows objects with
             undefined type and skips validation.
        """
        if path is None or (not isinstance(path, str) and
                            not isinstance(path, Path)):
            raise ValueError("Invalid value for 'path'. Please provide a valid "
                             "string or Path object.")
        if isinstance(path, str):
            path = Path(path)

        # Load built-in types.
        dsl.ConfigDefs.load_builtins()

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
        return HyperConfig(path.stem, config_values,
                           strict=strict,
                           line=0,
                           fname=path.as_posix())

    @staticmethod
    def load_str(text: str, strict: bool = True):
        """Parse a YAML-formatted string containing configuration objects.

        :param text: The YAML-formatted string containing configuration data.
        :type text: str

        :param strict: If True, strict parsing is enforced. Defaults to True.
        :type strict: bool, optional

        :return: An instance of HyperConfig containing
        the parsed configuration.
        :rtype: HyperConfig

        :raises HyperConfigError: If there are issues with
        parsing or validation.

        :Example:

        >>> config_text = '''
        ...     use: my_schema.yaml
        ...     some_obj:
        ...       some_opt: some_value
        ...     '''
        >>> config = HyperConfig.load_str(config_text)
        >>> print(config.some_obj.some_opt)
        'some_value'

        :Example with non-strict parsing:

        >>> config_text = 'some_key: some_value'
        >>> config = HyperConfig.load_str(config_text, strict=False)
        >>> print(config.some_key)
        'some_value'

        :note:
            - If `strict` is set to True (default), the parser requires that
              all objects are defined and raises an error for any validation
              or parsing issues.
            - If `strict` is set to False, the parser allows undefined objects
              in which case they are treated as plain dictionaries.
        """
        if text is None:
            raise ValueError("text is None")

        # Load built-in types.
        dsl.ConfigDefs.load_builtins()

        try:
            config_values = yaml.load(text, Loader=dsl._LineInfoLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            raise err.HyperConfError(
                f"Failed to parse YAML. Cause: {repr(e)}"
            )
        return HyperConfig(None, config_values,
                           strict=strict,
                           fname=None)

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
        self.__def__ = hdef

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
                # Require that all list elements are of type dict.
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
                self.update({ident: htype.convert(val)})

    def __getattr__(self, attr: str):
        """Return attribute value."""
        if attr is None:
            raise ValueError("attr is None")
        if attr not in self:
            raise AttributeError(
                f"Invalid configuration key '{attr}' for "
                f"configuraiton object {self.__def__}"
            )
        return self[attr]

    def __delitem__(self, v):
        """Not supported, read-only."""
        raise NotImplementedError("HyperConfig is read-only")


if __name__ == "__main__":
    config = HyperConfig.load_yaml("test_config.yaml")
