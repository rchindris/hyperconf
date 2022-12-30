"""Define custom hyperconf exceptions."""


class TemplateDefinitionError(Exception):
    """Thrown when a template definition file cannot be loaded."""

    def __init__(self, tag, line_no, path, message):
        """Initialize a TemplateDefinitionError.

        Args:
        tag (str): the tag name where the error occurs.
        line (int): line number where the tag is located.
        path (str): the path to the template definition file.
        msg (str): error details.
        """
        super().__init__(self, f"Failed to parse template definition for "
                         f"tag '{tag}':  {message} (in {path}, line {line_no}")
