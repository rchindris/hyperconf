"""Defing the HyperConf template language."""
import yaml
import typing as t

from pathlib import Path
try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")
import hyperconf.errors as err
from hyperconf.yaml import LineInfoLoader


class Keywords:
    """Define reserved keys."""

    validator = "_validator"
    typename = "_type"
    required = "_required"
    allow_multiple = "_allow_multiple"
    line = "__line__"
    use = "use"
    HDef = [validator, typename, required]


class HyperDef:
    """Provide type attributes."""

    def __init__(self, name,
                 typename=None,
                 line: int = -1,
                 fpath: str = None,
                 required: bool = False,
                 validator: str = None,
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
        self.definition_file = fpath
        self.line = line
        self.validator = validator
        self.options = options
        self.allow_multiple_values = allow_multiple_values

    def __repr__(self):
        """Debug str representation."""
        return f"{self.name} ({self.typename}) "\
            f"opts: {[o.name for o in self.options]}"

    @staticmethod
    def parse(tname, tdef, fname):
        """Parse a multi-option configuration object definition.

        :param tname:
          type name
        :param tdef:
          type definition, must be a dict
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
            raise ValueError("_tdef must be a dictionary")

        type_name = _tdef.get(Keywords.typename, tname)
        is_required = _tdef.get(Keywords.required, False)
        validator = _tdef.get(Keywords.validator, None)

        if validator:
            #TODO: make sure the validator exists.
            pass

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
                            "Please note that nesting definitions is not allowed.")
                opts.append(HyperDef(
                    name=aname,
                    typename=aval.get(aval[Keywords.typename], str),
                    required=aval.get(Keywords.required, True),
                    validator=aval.get(Keywords.validator, None),
                    line=opt_line,
                    fpath=fname))
            else:
                opts.append(HyperDef(name=aname, typename=aval))

        return HyperDef(name=tname,
                        typename=type_name,
                        required=is_required,
                        validator=validator,
                        options=opts)


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
    def parse_yaml(template_path: str, line: int, ref_file: str):
        """Load and parse referred template file.

        :param template_path:
        the path to the template file. It can be an absolute path,
        a relative path to the current working directory or a
        package resource (relative) path.
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
            pkg_path = pkg_files / "templates" / template_path.name

            if not pkg_path.exists():
                raise err.TemplateDefinitionError(
                    name=Keywords.use,
                    message=f"Failed to load template '{template_path}'. "
                    "Could not find a file or a resource with that name.",
                    line=line,
                    config_path=ref_file)

        with open(template_path) as tfile:
            try:
                return ConfigDefs.parse_dict(
                    yaml.load(tfile, Loader=LineInfoLoader),
                    fname=template_path.as_posix()
                )
            except yaml.scanner.ScannerError as e:
                raise err.TemplateDefinitionError(
                    name=Keywords.use,
                    message=f"Invalid YAML file: {e}",
                    line=line,
                    config_path=ref_file)
