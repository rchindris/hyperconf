"""Defing the HyperConf template language."""
import re
import yaml
import importlib
import typing as t

from yaml.loader import SafeLoader

from pathlib import Path
try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")
import hyperconf.errors as err


class _LineInfoLoader(SafeLoader):
    """Adds line numbers to parsed yaml dicts."""

    def construct_mapping(self, node, deep=False):
        """Augument parsed nodes."""
        mapping = super().construct_mapping(node, deep=deep)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


_id_synth = re.compile("^([_A-Za-z]+[_0-9A-Za-z]+)=?(.*)")

_module_names = ["re", "math", "pathlib"]
_eval_imports = {
    mod_name: importlib.import_module(mod_name)
    for mod_name in _module_names
}


class Keywords:
    """Define reserved keys."""

    validator = "validator"
    converter = "converter"
    typename = "type"
    required = "required"
    allow_multiple = "allow_many"
    line = "__line__"
    use = "use"
    HDef = [validator, converter, typename, required, allow_multiple]


class HyperDef:
    """Provide type attributes."""

    @staticmethod
    def parse(tname: str, tdef: dict, fname: str = None):
        """Parse a configuration object definition.

        :param tname: The name of the configuration object type.
        :type tname: str
        :param tdef: The dictionary specifying the configuration object definition.
        :type tdef: dict
        :param fname: The file name used for error reporting.
        :type fname: str

        :raises ValueError: If preconditions are not met.

        This method parses a definition named `tname`, specified as a dictionary
        using `tdef`. It checks if the dictionary contains the key
        :class:`Keywords.typename` and infers that the configuration object type
        name is the found value if it exists, or the specified argument `tname`
        if not. It also checks that :class:`Keywords.required` and
        :class:`Keywords.validator` exist and t
        The method then treats the rest of the dictionary keys as option specifiers.
        Each option must be of a previously defined type.
        Nesting definitions is not allowed.
        
        Example(s):
        >>> hyper_def.parse('nat', {
        ...     'validator': "hval >= 0"
        ... })
        >>> hyper_def.parse('mongo_db', {
        ...     "hostname": {
        ...         "_typename": "str",
        ...         "_required": True,
        ...     }
        ...     ...
        ... })
        """
        if tname is None:
            raise ValueError("tname is None")

        if tdef is None:
            raise ValueError("tdef is None")

        _tdef = tdef.copy()
        if Keywords.line in _tdef:
            def_line = _tdef[Keywords.line]
            del _tdef[Keywords.line]

        if tname is None:
            raise ValueError("tname is None")
        if _tdef is None or not isinstance(_tdef, dict):
            raise ValueError("tdef must be a dictionary")

        type_name = _tdef.get(Keywords.typename, tname)
        is_required = _tdef.get(Keywords.required, False)
        validator = _tdef.get(Keywords.validator, None)
        converter = _tdef.get(Keywords.converter, None)

        for k in Keywords.HDef:
            if k in _tdef:
                del _tdef[k]

        # Parse options.
        opts = []
        for aname, aval in _tdef.items():
            if aval.__class__ not in [str, dict]:
                raise err.TemplateDefinitionError(
                    name=tname,
                    line=def_line,
                    message="Invalid type definition. Unsupported "
                    f"YAML type '{_tdef.__class__}' for option definition.")

            if isinstance(aval, dict):
                opt_line = def_line
                if Keywords.line in aval:
                    opt_line = aval[Keywords.line]
                    del aval[Keywords.line]

                # An option specified as dict.
                for akey in aval.keys():
                    if akey not in Keywords.HDef:
                        raise err.TemplateDefinitionError(
                            name=tname,
                            line=opt_line,
                            message="Invalid option definition: "
                            f"found unexpected key '{akey}'. "
                            "Please note that nesting definitions is "
                            "not allowed.")
                opts.append(HyperDef(
                    name=aname,
                    typename=aval.get(Keywords.typename, str),
                    required=aval.get(Keywords.required, True),
                    validator=aval.get(Keywords.validator, None),
                    converter=aval.get(Keywords.converter, None),
                    line=opt_line,
                    fpath=fname))
            else:
                opts.append(HyperDef(name=aname, typename=aval))

        return HyperDef(name=tname,
                        typename=type_name,
                        required=is_required,
                        validator=validator,
                        converter=converter,
                        options=opts)

    @staticmethod
    def infer_type(decl_tag: str, decl: str = None, hdef = None):
        """Determine the definition for the given tag.

        A declaration has the syntax
        
         decl_name[=def_name]: ...
           
        If def_name is specified then the decl_name can be any valid
        identifier, otherwise decl_name designates the definition to use,
        e.g.:

        database_config:
        ...
        database_config1=database_config:
        ...
        results in two distinct objects of the same type, 'database_config',
        but with different tags, 'database_config' and 'database_config1'
        respectively.

        :param decl_tag:
        the object or option name.
        :param decl:
        the value of the option or object.
        :param hdef:
        the object definition or parent definition in case of an option.
        """
        if decl_tag is None:
            raise ValueError("decl_tag is None")

        # Try to determine type from the tag.
        ident, htype = _id_synth.match(decl_tag).groups()
        if not htype and ConfigDefs.contains(ident):
            htype = ident

        if not htype and hdef:
            # Failed to determine type from name/tag.
            # Search the definition of the enclosing decl
            # for an option with that name.
            opt = [o for o in hdef.options if o.name == ident]
            if opt:
                htype = opt[0].typename

        if not htype:
            # Default to the actual datatype.
            htype = decl.__class__.__name__
            
        return ident, ConfigDefs.get(htype) if htype else None

    def __init__(self, name,
                 typename=None,
                 line: int = -1,
                 fpath: str = None,
                 required: bool = False,
                 validator: str = None,
                 converter: str = None,
                 allow_multiple_values: bool = False,
                 options: t.List = []):
        """ Initialize a configuration object definition.

        :param name:
         the object name. Must start with a letter or '_' and
         cannot contain whitespace and special characters.
        :para typename:
         the atomic type in case of single-option definitions.
        :param required:
         whether this is a mandatory configuration object or not.
         Default: False.
        :param file:
         the path to the file containing this definition.
        :param line:
         the line at which the definition is specified.
        """
        self.name = name
        self.typename = typename
        self.requiredred = required
        self.def_file = fpath
        self.line = line
        self._validator = validator
        self._converter = converter
        self.options = options
        self.allow_multiple_values = allow_multiple_values

    def __repr__(self):
        """Debug str representation."""
        return f"({self.name} "\
            f"{[o.name for o in self.options]})"

    def validate(self, decl: dict, line: int=0, filename: str = None):
        """Validate the structure and values from declaration."""
        if not self._validator:
            return True

        # validate structure
        if type(decl) is dict:
            decl_opts = list(decl.keys())
            
            # any required opt not specified => error
            for opt in self.options:
                if not opt in decl_opts:
                    raise err.ConfigurationError(
                        f"Missing required option {opt}",
                        line=decl.line, fname=filename
                    )
                decl_opts.remove(opt)

            # check if remaining are valid opt names
            if any([opt not in self.options
                    for opt in decl_opts]):
                opt_names = [o for o in decl_opts
                             if not o in self.options]
                raise err.ConfigurationError(
                    f"Unkown options {opt_names} for definition {self}.",
                    line=line,
                    filename=filename
                )

        is_valid = True
        err_msg = None
        try:
            context = _eval_imports.copy()
            context.update({
                "htype": self,
                "hval": decl,
            })
            val_result = eval(
                self._validator,
                context
            )
            if isinstance(val_result, tuple):
                is_valid, err_msg = val_result
            else:
                is_valid = val_result
                
            # Consider only bool values for False.
            if not is_valid and\
               not isinstance(is_valid, bool):
                is_valid = True
        except Exception as e:
            err_msg = e

        if not is_valid:
            raise err.ConfigurationError(
                f"Invalid configuration value '{decl}' "
                f"for type {self} "
                f"{': ' + (str(err_msg) if err_msg else '')}",
                line=line,
                fname=filename
            )
        
    def convert(self, decl, line: int=0, filename: str = None):
        """Convert option value."""
        if decl is None:
            raise ValueError("decl is None")
        if not self._converter:
            return decl
        try:
            context = _eval_imports.copy()
            context.update({
                "htype": self,
                "hval": decl,
            })
            res = eval(
                self._converter,
                context
            )
            return res
        except Exception as e:
            raise err.ConfigurationError(
                f"Could not convert value '{decl}' "
                f"for type {self}: {e}",
                line=line,
                fname=filename
            )


class ConfigDefs:
    """Template definition parser and type registry."""

    _typedefs = {}

    @staticmethod
    def add(hdefs):
        """Register a definition or list of definitions.

        :param hdefs:
          definition or a collection of definitions.
        """
        if hdefs is None:
            raise ValueError("hdefs is None")
        if not isinstance(hdefs, list):
            hdefs = [hdefs]

        for hdef in hdefs:            
            if hdef.name in ConfigDefs._typedefs:
                raise err.DuplicateDefError(
                    ConfigDefs._typedefs[hdef.name], hdef
                )
            ConfigDefs._typedefs[hdef.name] = hdef

    @staticmethod
    def get(tag: str):
        """Return the definition for the tag or None."""
        if tag is None:
            raise ValueError("tag is None")
        return ConfigDefs._typedefs.get(tag, None)

    @staticmethod
    def contains(def_name: str):
        """Check if the name is defined.

        :param def_name:
         the object definition name.
        """
        if def_name is None:
            raise ValueError("def_name is None")
        return def_name in ConfigDefs._typedefs

    @staticmethod
    def clear():
        """Remove all known type bindings."""
        ConfigDefs._typedefs.clear()
        ConfigDefs._loaded_files.clear()

    @staticmethod
    def parse_dict(defs: t.Dict, fname: str = None):
        """Parse type definitions.

        :param defs: a dictionary containing type structure
        information (as nested dictionaries).

        :return: a list of :class:TypeDef definitions.
        """
        if defs is None:
            raise ValueError("defs is None")

        if not isinstance(defs, dict):
            raise err.TemplateDefinitionError(
                name=fname,
                line=0,
                message=f"Invalid value type for 'defs': {defs.__class__}."
                "Configuration template definitions must contain "
                "definitions as top level YAML objects")

        typedefs = []
        def_line = 0

        for tname, tdef in defs.items():
            if tname == Keywords.line:
                def_line = tdef
                continue

            if tname == "use":
                # Load referenced definitions.
                if not isinstance(tdef, str):
                    raise err.TemplateDefinitionError(
                        name=Keywords.use,
                        message=f"The built-in '{Keywords.use}' directive"
                        "must specify a file path.",
                        line=def_line)
                ConfigDefs.parse_yaml(tdef, line=def_line, ref_file=fname)
                continue

            if isinstance(tdef, dict):
                typedefs.append(HyperDef.parse(tname, tdef, fname))
            elif isinstance(tdef, str):
                typedefs.append(HyperDef(name=tname, typename=tdef))
            else:
                raise err.TemplateDefinitionError(
                    name=tname,
                    line=def_line,
                    message="Invalid type definition. Unsupported "
                    f"YAML type {tdef.__class__} for type definition.")

        ConfigDefs.add(typedefs)
        return typedefs

    @staticmethod
    def load_builtins():
        """Load built-in types."""
        ConfigDefs.parse_yaml("builtins")

    _loaded_files = []
    @staticmethod
    def parse_yaml(template_path: str, line: int = 0, ref_file: str = None):
        """Load definitions from path.

        :param template_path:
        the path to the template file. It can be an absolute path,
        a relative path to the current working directory or a
        package resource.
        :param line:
        the line at which the use directive occurs.
        :param ref_file:
        the file that contains the use directive.
        """
        if not template_path.endswith(".yaml"):
            template_path = template_path + ".yaml"

        template_path = Path(template_path) if \
            isinstance(template_path, str) else template_path

        if not template_path.exists():
            # Search for a packaged resource
            # having the same name (predefined template).
            pkg_files = resources.files("hyperconf")
            template_path = pkg_files / template_path.name

            if not template_path.exists():
                raise err.TemplateDefinitionError(
                    name=Keywords.use,
                    message=f"Failed to load template '{template_path}'. "
                    "Could not find a file or a resource with that name.",
                    line=line,
                    config_path=ref_file)

        if template_path not in ConfigDefs._loaded_files:
            ConfigDefs._loaded_files.append(template_path)
            with open(template_path) as tfile:
                try:
                    return ConfigDefs.parse_dict(
                        yaml.load(tfile, Loader=_LineInfoLoader),
                        fname=template_path.as_posix()
                    )
                except yaml.scanner.ScannerError as e:
                    raise err.TemplateDefinitionError(
                        name=Keywords.use,
                        message=f"Invalid YAML file: {e}",
                        line=line,
                        config_path=ref_file)

    @staticmethod
    def parse_str(text: str):
        """Parse YAML formatted string.

        :param text:
        the YAML to parse.
        """
        if text is None:
            raise ValueError("text is None")

        return ConfigDefs.parse_dict(
            yaml.load(text, Loader=_LineInfoLoader)
        )
