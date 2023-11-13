"""Defing the HyperConf template language."""
import typing as t

import hyperconf.errors as err


class Keywords:
    """Define reserved keys."""

    validator = "_validator"
    typename = "_type"
    required = "_required"
    HDef = [validator, typename, required]


class hdef:
    """Provide type attributes."""

    def __init__(self, name,
                 typename=None,
                 line: int = -1,
                 fpath: str = None,
                 required: bool = False,
                 validator: str = None,
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
        self.file = fpath
        self.line = line
        self.validator = validator
        self.options = options

    def __repr__(self):
        return f"{self.name}: {self.typename}"


class TypeRegistry:
    """Manage known definitons."""

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
            print("register ", hdef)
            print("contents: ", [(k, v) for k, v in TypeRegistry._typedefs.items()])
            if hdef.name in TypeRegistry._typedefs:
                print("duplicate ", hdef.name, TypeRegistry._typedefs[hdef.name])
                raise err.DuplicateDefError(
                    TypeRegistry._typedefs[hdef.name], hdef
                )
            TypeRegistry._typedefs[hdef.name] = hdef

    @staticmethod
    def contains(def_name: str):
        """Check if the name is defined.

        :param def_name:
         the object definition name.
        """
        if def_name is None:
            raise ValueError("def_name is None")
        return def_name in TypeRegistry._typedefs

    @staticmethod
    def clear():
        """Remove all known type bindings."""
        TypeRegistry._typedefs.clear()


def _parse_complex_def(tname, tdef, fname):
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
    if "__line__" in _tdef:
        def_line = _tdef["__line__"]
        del _tdef["__line__"]

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
            # An option specified as dict.
            for akey in aval.keys():
                if akey not in Keywords.HDef:
                    raise err.TemplateDefinitionError(
                        name=tname,
                        line=def_line,
                        message="Invalid option definition: "
                        f"found unexpected key '{akey}'. "
                        "Please note that nesting definitions is not allowed.")
            opts.append(hdef(typename=aval["typename"],
                             required=aval.get("required", True),
                             validator=aval.get("validator", ""),
                             line=def_line,
                             fpath=fname))
        else:
            opts.append(hdef(name=aname, typename=aval))

    return hdef(name=tname,
                typename=type_name,
                required=is_required,
                validator=validator,
                options=opts)


def parse_definitions(defs: t.Dict, fname: str = None):
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
        if tname == "__line__":
            def_line = tdef
            continue

        if isinstance(tdef, dict):
            print("parsing ", tname, tdef)
            definition = _parse_complex_def(tname, tdef, fname)
            typedefs.append(definition)
        elif isinstance(tdef, str):
            typedefs.append(hdef(name=tname, typename=tdef))
        else:
            raise err.TemplateDefinitionError(
                name=tname,
                line=def_line,
                message="Invalid type definition. Unsupported "
                f"YAML type {tdef.__class__} for type definition.")
    TypeRegistry.add(typedefs)
    return typedefs
