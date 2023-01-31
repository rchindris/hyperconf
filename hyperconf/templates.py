"""Provide configuration tag definition support."""
import yaml
import logging

from pathlib import Path
from typing import Dict, List

from enum import Enum

try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")

from hyperconf.yaml import LineInfoLoader
from hyperconf.types import (
    htype,
    hstr
)
from hyperconf.errors import (
    TemplateDefinitionError,
    UndefinedTagError
)


_logger = logging.getLogger(__name__)


class ParamDef:
    """A configuration element parameter definition."""

    def __init__(self, node: Dict, element):
        """Initialize tag argument from spec.

        Args:
        node (Dict): a dictionary containing argument
        definition properties. Any argument must have a
        name, a type and a default value.
        element (ElementDefinition): the tag definition
        that contains this argument definition.
        """
        if node is None:
            raise ValueError("node is None")
        if element is None:
            raise ValueError("element is None")

        self._line = node["__line__"]
        if "name" not in node:
            raise TemplateDefinitionError(element.name,
                                          self._line,
                                          element.file,
                                          "Missing the 'name' property "
                                          "for argument.")
        self._name = node["name"]

        type_name = node.get("type", "str")

        if not htype.supports(type_name):
            raise TemplateDefinitionError(
                element.name,
                self._line,
                element.file,
                f"Unknown data type '{type_name}."
            )

        self._type = htype.from_name(type_name)
        self._required = node.get("required", False)
        self._default_value = node.get("default-value",
                                       self._type.value.python_type())

    @property
    def name(self):
        """Argument name."""
        return self._name

    @property
    def type(self):
        """Argument type."""
        return self._type

    @property
    def required(self):
        """Return True if the parameter is required."""
        return self._required

    @property
    def default_value(self):
        """Parameter default value."""
        return self._default_value


class NodeDef:
    """Configuration template element definition."""

    def __init__(self, name: str, node: Dict, template_path: str = None):
        """Initialize an ElementDefinition.

        Arguments:
        name (str): the configuration tag name.
        required (bool): whether this element is a required configuration
        element or not. Default: False.
        argments (List[Dict]): a list of supported arguments. Default: empty.
        """
        if node is None:
            raise ValueError("node is None")

        self._file = template_path
        self._name = name
        self._type_name = node.get("type", hstr.name)
        if not htype.supports(self._type_name):
            raise TemplateDefinitionError(self._name,
                                          node["__line__"], self._file,
                                          f"The type {self._type_name} is "
                                          "not supported")
        self._required = node.get("required", False)

        self._line = node.get("__line__")
        self._args = []

        if "args" in node:
            arg_defs = node["args"]
            if not isinstance(arg_defs, list):
                raise TemplateDefinitionError(
                    "args",
                    arg_defs["__line__"], self._file,
                    "The component definition arguments must be "
                    "specified as a list.")

        for arg_name, arg_def in node.items():
            if arg_name == "args":
                for arg in arg_def:
                    self._args.append(ParamDef(arg, self))

    def __repr__(self):
        """Object representation."""
        text = f"[tag: {self._name}, type:{self._type_name}, args: ("
        for elem in self._args:
            text += str(elem)
        text += ")]"
        return text

    def __str__(self):
        """Convert to string."""
        return f"ElementDefinition:{self._name}"

    def parse(self, decl):
        """Validate and extract a node declaration."""
        if decl is None:
            raise ValueError("decl is None")
        print(decl, self._type_name)
        return decl

    @property
    def name(self):
        """Tag name."""
        return self._name

    @property
    def type(self):
        """Element type name."""
        return self._type_name

    @property
    def file(self):
        """Definition file."""
        return self._file

    @property
    def line_number(self):
        """Definition line number."""
        return self._line


class NodeDefs:
    """Define the elements allowed in an experiment configuration file."""

    class Predefined:
        """Builtin tokens."""

        USE = "use"

    def __init__(self, template_file: str | Path | List[str] | List[Path]
                 = "builtins.yaml"):
        """Initialize an experiment template from file.

        Arguments:
        template_file (str | Path | List[str] | List[Path]): the path or paths
        to a template definition file.
        """
        if template_file is None:
            raise ValueError("template_file is None")

        if not isinstance(template_file, str) and\
           not isinstance(template_file, Path) and\
           not isinstance(template_file, list):
            raise ValueError("template_file must be a string, Path "
                             " or a list containing string or Path objects.")
        if isinstance(template_file, list) and\
           any([not isinstance(x, str) and not isinstance(x, Path)
                for x in template_file]):
            raise ValueError("template_file contains unsupported values: only"
                             "str and Path objects are allowed")

        if not isinstance(template_file, list):
            template_files = [Path(template_file) if
                              isinstance(template_file, str)
                              else template_file]
        else:
            template_files = [Path(f) if isinstance(f, str)
                              else f for f in template_file]

        if not any([t.as_posix() == "builtins.yaml" for t in template_files]):
            template_files.append(Path("builtins.yaml"))

        self._names = []
        self._descriptions = []
        self._tags = {}

        for template_path in template_files:
            self.parse(template_path)

    def __repr__(self):
        """Object representation."""
        return f"ConfigurationTemplate({self._names!r})"

    def __str__(self):
        """Object to string."""
        return f"ConfigurationTemplate: templates={self._names}"

    def __getitem__(self, tag_name):
        """Get a tag by name."""
        if tag_name not in self._tags:
            raise UndefinedTagError(tag_name)
        return self._tags[tag_name]

    def __setitem__(self, key, value):
        """Not supported."""
        raise NotImplementedError(
            "Adding a tag definition directly is not supported"
        )

    def parse(self, template_path: str | Path):
        """Load a configuration template file.

        Args:
        template_path (str | Path): the path to the template definition file.
        """
        if template_path is None:
            raise ValueError("template_path is None")

        template_path = Path(template_path) if \
            isinstance(template_path, str) else template_path

        if not template_path.exists():
            # Search for a packaged resource
            # having the same name (predefined template).
            pkg_files = resources.files("hyperconf")
            template_path = pkg_files / "templates" / template_path.name

            if not template_path.exists():
                raise IOError(f"Failed to load template {template_path}: "
                              "Please check that the file exists and is a "
                              "valid configuration template definition file.")

        with open(template_path) as tfile:
            try:
                _logger.info(f"Loading configuration template from {tfile}.")
                template_def = yaml.load(tfile, Loader=LineInfoLoader)
            except yaml.scanner.ScannerError as e:
                raise IOError(f"Invalid YAML file: {e}")

        for tag_name, node in template_def.items():
            if tag_name == "__line__":
                continue
            elif tag_name == "name":
                self._names.append(node)
            elif tag_name == "description":
                self._descriptions.append(node)
            else:
                if tag_name in self._tags:
                    existing_tag = self._tags[tag_name]
                    raise TemplateDefinitionError(
                        tag_name,
                        template_def["__line__"],
                        template_path,
                        "Duplicate tag definition. This tag is already "
                        f"defined in {existing_tag.file} at line "
                        f"{existing_tag.line_number}"
                    )
                self._tags[tag_name] = NodeDef(
                    tag_name, node, template_path)


if __name__ == "__main__":
    template = NodeDefs(["ml.yaml"])
    print(template)
