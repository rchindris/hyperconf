"""Define custom hyperconf exceptions."""


class HyperconfError(Exception):
    """Base exception class for HyperConf package."""

    def __init__(self, message):
        """Initialize a Hyperconf exception.

        Args:
        tag (str): the tag name where the error occurs.
        line (int): line number where the tag is located.
        path (str): the path to the template definition file.
        msg (str): error details.
        """
        super().__init__(self, message)


class TemplateDefinitionError(HyperconfError):
    """Thrown when a template definition file cannot be loaded."""

    def __init__(self, tag, line_no, path, message):
        """Initialize a TemplateDefinitionError.

        Args:
        tag (str): the tag name where the error occurs.
        line (int): line number where the tag is located.
        path (str): the path to the template definition file.
        msg (str): error details.
        """
        super().__init__(f"Failed to parse template definition for "
                         f"tag '{tag}':  {message} (in {path}, line "
                         f"{line_no})")


class UndefinedTagError(HyperconfError):
    """Signals that a node name is undefined."""

    def __init__(self, tag_name, line_no, path):
        """Initialize an UndefinedTagError.

        Args:
        tag_name (str): the name of the undefined tag.
        """
        super().__init__
        (
            f"Could not find a definition for tag {tag_name}  "
            f"(in {path}, line {line_no})"
        )


class InvalidYamlError(HyperconfError):
    """Thrown when an YAML configuration file cannot be loaded."""

    def __init__(self, path, error):
        """Initialize an InvalidYamlError.

        Args:
        tag_name (str): the undefined node name.
        """
        super().__init__
        (
            f"Failed to load the configuration from {path}. "
            f"Reason: {error}"
        )


class UnknownDataTypeError(HyperconfError):
    """Signal an unsupported hyperconf data type."""

    def __init__(self, type_name: str):
        """Initialize an UnknownDataTypeError exception.

        Arguments:
        type_name (str): the unknown type name.
        """
        super().__init__(f"The data type {type_name} is not supported.")
