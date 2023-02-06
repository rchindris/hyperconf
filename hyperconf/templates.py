"""Provide configuration tag definition support."""
import yaml
import logging

from pathlib import Path
from typing import Dict, List

try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")

from hyperconf.yaml import LineInfoLoader
from hyperconf.lang import (
    hType, hStr,
    Keywords
)
from hyperconf.errors import (
    TemplateDefinitionError,
    UndefinedTagError
)


_logger = logging.getLogger(__name__)


class ParameterDefinition:
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
        self._name = node[Keywords.Parameter.NAME.value]
        type_name = node.get(Keywords.Parameter.TYPE, hStr.name)

        if not hType.is_supported(type_name):
            raise TemplateDefinitionError(
                element.name,
                self._line,
                element.file,
                f"Parameter type '{type_name} is not supported."
            )

        self._type = hType.from_name(type_name)
        self._required = node.get(Keywords.Parameter.REQUIRED, False)
        self._default_value = node.get(
            Keywords.Parameter.DEFAULT_VALUE,
            self._type.default_value
        )

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


class NodeTemplate:
    """Configuration object template definition."""

    def __init__(self, name: str, node: Dict, template_path: str = None):
        """Initialize a NodeTemplate.

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
        self._description = node.get(Keywords.Template.DESCRIPTION.value, "")

        self._type_name = node.get(Keywords.Template.TYPE.value, hStr.name)
        if not hType.is_supported(self._type_name):
            raise TemplateDefinitionError(self._name,
                                          node["__line__"], self._file,
                                          f"The type {self._type_name} is "
                                          "not supported")
        self._type = hType.from_name(self._type_name)

        self._required = node.get(Keywords.Template.REQUIRED, False)

        self._line = node.get("__line__")
        self._params = []

        if Keywords.Template.ARGS in node:
            arg_defs = node[Keywords.Template.ARGS]
            if not isinstance(arg_defs, list):
                raise TemplateDefinitionError(
                    "args",
                    arg_defs["__line__"], self._file,
                    "The component definition arguments must be "
                    "specified as a list.")

        for arg_name, arg_def in node.items():
            if arg_name == Keywords.Template.ARGS:
                for arg in arg_def:
                    self._params.append(ParameterDefinition(arg, self))

    def __repr__(self):
        """Object representation."""
        text = f"[tag: {self._name}, type:{self._type_name}, "\
            f"description: '{self._description}', args: ("

        for elem in self._params:
            text += str(elem)
        text += ")]"
        return text

    def __str__(self):
        """Convert to string."""
        return f"ObjectTemplate: {self._name} - {self._description}"

    def parse(self, decl):
        """Validate and extract a node declaration."""
        if decl is None:
            raise ValueError("decl is None")

        if not isinstance(decl, dict):
            return self._type(decl)
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


class NodeTemplates:
    """Define the elements allowed in an experiment configuration file."""

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
        self._node_defs = {}

        for template_path in template_files:
            self.load_definitions(template_path)

    def __repr__(self):
        """Object representation."""
        return f"ConfigurationTemplate({self._names!r})"

    def __str__(self):
        """Object to string."""
        return f"ConfigurationTemplate: templates={self._names}"

    def __getitem__(self, tag_name):
        """Get a tag by name."""
        if tag_name not in self._node_defs:
            raise UndefinedTagError(tag_name)
        return self._node_defs[tag_name]

    def __setitem__(self, key, value):
        """Not supported."""
        raise NotImplementedError(
            "Adding a tag definition directly is not supported"
        )

    def get(self, key, default_val):
        """Return the value for the key or default value."""
        if key not in self._node_defs:
            return default_val
        return self._node_defs[key]

    def load_uses(self, config: Dict):
        """Load templates as indicated by the 'use' directive.

        Arguments:
        config (dict): parsed yaml config data.
        """
        if config is None or not isinstance(config, dict):
            raise ValueError("config must be a dict")
        if Keywords.Template.USE.value not in config:
            return

        use_decl = config[Keywords.Template.USE.value]
        use_def = self._node_defs[Keywords.Template.USE.value]

        use_paths = use_def.parse(use_decl)
        for template_path in use_paths:
            if not template_path.endswith(".yaml"):
                template_path = f"{template_path}.yaml"
            self.load_definitions(template_path)
        del config[Keywords.Template.USE.value]

    def load_definitions(self, template_path: str | Path):
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
                if tag_name in self._node_defs:
                    existing_tag = self._node_defs[tag_name]
                    raise TemplateDefinitionError(
                        tag_name,
                        template_def["__line__"],
                        template_path,
                        "Duplicate tag definition. This tag is already "
                        f"defined in {existing_tag.file} at line "
                        f"{existing_tag.line_number}"
                    )
                self._node_defs[tag_name] = NodeTemplate(
                    tag_name, node, template_path)


if __name__ == "__main__":
    template = NodeTemplates(["ml.yaml"])
    print(template)
