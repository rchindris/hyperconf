"""Provide experiment configuration templates support."""
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from typing import Dict, List
try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")

from hyperconf.errors import TemplateDefinitionError


class _LoadLineInfo(SafeLoader):
    """Adds line numbers to parsed yaml dicts."""

    def construct_mapping(self, node, deep=False):
        """Augument parsed nodes."""
        mapping = super().construct_mapping(node, deep=deep)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


class ArgumentDefinition:
    """A configuration element parameter definition."""
    def __init__(self, node: Dict, path: str | Path):
        """Initialize from spec.

        Args:
        node (Dict): a dictionary containing argument
        definition properties. Any argument must have a
        name, a type and a default value.
        """
        if node is None:
            raise ValueError("node is None")
        if "name" not in node:
            raise TemplateDefinitionError("args",
                                          node["__line__"],
                                          path, "Property 'name' is required")


class ElementDefinition:
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

        self._name = name
        self._type = node.get("type", str)
        self._required = node.get("required", False)
        self._file = template_path
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
                    self._args.append(ArgumentDefinition(arg, self._file))

    def __repr__(self):
        """Object representation."""
        text = f"[tag: {self._name}, type:{self._type}, args: ("
        for elem in self._args:
            text += str(elem)
        text += ")]"
        return text

    def __str__(self):
        """Convert to string."""
        return f"ElementDefinition:{self._name}"

    @property
    def name(self):
        """Tag name."""
        return self._name

    @property
    def type(self):
        """Element type name."""
        return self._type

    @property
    def file(self):
        """Definition file."""
        return self._file

    @property
    def line_number(self):
        """Definition line number."""
        return self._line


class ConfigurationDefinitions:
    """Define the elements allowed in an experiment configuration file."""

    def __init__(self, template_file: str | Path | List[str] | List[Path]):
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
            raise ValueError("template_file must be a string or Path object")
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

    def parse(self, template_path: str | Path):
        """Load a template file.

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
                template_def = yaml.load(tfile, Loader=_LoadLineInfo)
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
                self._tags[tag_name] = ElementDefinition(
                    tag_name, node, template_path)


if __name__ == "__main__":
    template = ConfigurationDefinitions(["generic.yaml", "keras.yaml"])
    print(template)
