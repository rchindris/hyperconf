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
                         f"tag '{tag}':  {message} (in {path}, line {line_no}")


class UndefinedTagError(HyperconfError):
    """Thrown when a tag is not defined."""

    def __init__(self, tag_name):
        """Initialize an UndefinedTagError.

        Args:
        tag_name (str): the name of the undefined tag.
        """
        super().__init__
        (
            self,
            f"Could not find a definition for tag {tag_name}"
        )


class InvalidYamlError(HyperconfError):
    """Thrown when an YAML configuration file cannot be loaded."""

    def __init__(self, path, error):
        """Initialize an InvalidYamlError.

        Args:
        tag_name (str): the name of the undefined tag.
        """
        super().__init__
        (
            self,
            f"Failed to load the configuration from {path}. "
            f"Reason: {error}"
        )
