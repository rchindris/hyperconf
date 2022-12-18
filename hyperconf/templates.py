"""Provide experiment configuration templates support."""
import yaml
from pathlib import Path
from typing import Dict, List
try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")


class ElementDefinition:
    """Configuration template element definition."""

    def __init__(self, name: str, arguments: Dict = {}):
        """Initialize an ElementDefinition.

        Arguments:
        name (str): the configuration item name.
        required (bool): whether this element is a required configuration
        element or not. Default: False.
        argments (List[Dict]): a list of supported arguments. Default: empty.
        """
        if name is None:
            raise ValueError("name is None")
        if arguments is None:
            raise ValueError("arguments is None")

        self._name = name
        self._type = arguments.get("type", "str")
        self._required = arguments.get("required", False)

        self._args = []

        for arg_name, arg_def in arguments.items():
            if arg_name in ["type", "required"]:
                continue
            if arg_name == "args":
                for component_def in arg_def:
                    self._args.append(ElementDefinition(component_def))
            else:
                raise ValueError(f"unsupported element definition: {arg_name}:"
                                 "expecting a 'args' tag.")

    def __repr__(self):
        """Serialize to string."""
        text = f"[tag: {self._name}, type:{self._type}, args: ("
        for elem in self._args:
            text += str(elem)
        text += ")]"
        return text

    @property
    def name(self):
        """Tag name."""
        return self._name

    @property
    def type(self):
        """Element type name."""
        return self._type


class ConfigurationDefinitions:
    """Define the format of an experiment configuration."""

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
            self.load(template_path)

    def _parse(self, template_dict):
        if "name" not in template_dict:
            raise ValueError("Invalid template: expecting a 'name' key.")

        for tag_name, content in template_dict.items():
            if tag_name == "name":
                self._names.append(content)
            elif tag_name == "description":
                self._descriptions.append(content)
            else:
                self._tags[tag_name] = ElementDefinition(tag_name, content)

    def __repr__(self):
        """Object representation."""
        return "ConfigurationTemplate(templates: " +\
            ", ".join([f"({n}, {d})" for n, d in
                       zip(self._names, self._descriptions)]) +\
                       ", tags: [" + ", ".join(self._tags) + "])"

    def __str__(self):
        """Object to string."""
        return f"Configuration template: name={self._name} "\
            f"description= {self._description}"

    def load(self, template_path: str|Path):
        if not template_path.exists():
            # Search for a package resource
            # with the same name (predefined template).
            pkg_files = resources.files("hyperconf")
            template_path = pkg_files / "templates" /\
                template_path.name

            if not template_path.exists():
                raise IOError(f"Failed to load template {template_path}: "
                              "The file cannot be found and no builtin "
                              "template with that name exists.")

            with open(template_path) as tfile:
                try:
                    template_def = yaml.load(tfile, yaml.CLoader)
                except yaml.scanner.ScannerError as e:
                    raise IOError(f"Invalid YAML file: {e}")

            self._parse(template_def)



if __name__ == "__main__":
    template = ConfigurationDefinitions(["generic.yaml", "keras.yaml"])
    print(repr(template))
