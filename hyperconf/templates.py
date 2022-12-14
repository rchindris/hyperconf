"""Provide experiment configuration templates support."""
import yaml
from typing import Dict
from pathlib import Path
try:
    from importlib import resources
except ImportError:
    raise ImportError("Could not find module importlib.resources."
                      "Python versions <3.7 are not supported.")


class ExperimentItem:
    """Configuration for an experiment item."""

    def __init__(self, props: Dict):
        """Initialize an ExperimentItem.

        Arguments:
        properties (Dict): a dictionary containing formatting properties.
        """
        if props is None:
            raise ValueError("properties is None")

        self._name = None
        self._type = None
        self._required = False

        self._tags = []

        for prop_name, prop_def in props.items():
            if prop_name == "name":
                self._name = props["name"]
            elif prop_name == "required":
                self._required = props["required"]
            elif prop_name == "type":
                self._type = props["type"]
            elif prop_name == "components":
                for component_def in prop_def:
                    self._tags.append(ExperimentItem(component_def))
            else:
                raise ValueError("unsupported element definition: "
                                 f"{prop_name}")

    def __repr__(self):
        """Serialize to string."""
        text = f"{self._name}\ntype:{self._type}\ntags:\n\t"
        for tag in self._tags:
            text += str(tag)
        return text


class ExperimentTemplate:
    """Define the format of an experiment configuration."""

    def __init__(self, template_file: str | Path):
        """Initialize an experiment template from file.

        Arguments:
        template_file (str|Path): the path to a template
        definition YAML file.
        """
        if template_file is None:
            raise ValueError("template_file is None")

        if not isinstance(template_file, str) and\
           not isinstance(template_file, Path):
            raise ValueError("template_file must be a string or Path object")

        if isinstance(template_file, str):
            template_resource = Path(template_file)
        else:
            template_resource = template_file

        if not template_resource.exists():
            # Search for a package resource
            # with the same name (predefined template).
            pkg_files = resources.files("hyperconf")
            template_resource = pkg_files / "templates" /\
                template_resource.name

            if not template_resource.exists():
                raise IOError(f"Failed to load template {template_resource}: "
                              "The file cannot be found and no builtin "
                              "template with that name exists.")

        with open(template_resource) as tfile:
            try:
                template_def = yaml.load(tfile, yaml.CLoader)
            except yaml.scanner.ScannerError as e:
                raise IOError(f"Invalid YAML file: {e}")

        self._parse(template_def)

    def _parse(self, template_dict):
        if "name" not in template_dict:
            raise ValueError("Invalid template: expecting a 'name' key.")

        self._description = None
        self._tags = {}

        for tag_name, content in template_dict.items():
            if tag_name == "name":
                self._name = content
            elif tag_name == "description":
                self._description = content
            else:
                self._tags[tag_name] = ExperimentItem(content)

    def __repr__(self):
        """Describe the template contents."""
        text = f"Template name: {self._name}"
        f"Description: {self._description}"
        for tag_name, tag in self._tags.items():
            text += f"\n\t{tag_name}: {str(tag)}"
        return text


if __name__ == "__main__":
    template = ExperimentTemplate("objdetect.yaml")
    print(template)
