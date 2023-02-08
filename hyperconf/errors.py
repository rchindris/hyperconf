"""Define custom hyperconf exceptions."""


class HyperConfError(Exception):
    """Base exception class for HyperConf package."""

    def __init__(self, message: str,
                 line: int = None, config_path: str = None):
        """Initialize a Hyperconf exception.

        Args:
        message (str): the tag name where the error occurs.
        """
        line_info = ""
        if line:
            line_info += f"at line {str(line)}"
        if config_path:
            line_info += f", in '{str(config_path)}'"

        message = f"{message} ({line_info})" if\
            line_info != "" else message
        super().__init__(message)


class TemplateDefinitionError(HyperConfError):
    """Thrown when a template definition file cannot be loaded."""

    def __init__(self, name: str, message: str, line: int,
                 config_path: str = None):
        """Initialize a TemplateDefinitionError.

        Arguments:
        name (str): the tag name where the error occurs.
        messagfe (str): the error message.
        line (int): line number where the tag is located.
        cofnig_path (str): the path to the template definition file.
        """
        super().__init__
        (
            f"Failed to parse template definition for "
            f"tag '{name}':  {message}",
            line, config_path
        )


class UndefinedTagError(HyperConfError):
    """Signals that a node name is undefined."""

    def __init__(self, name: str, line: int, config_path: str = None):
        """Initialize an UndefinedTagError.

        Arguments:
        name (str): the name of the undefined tag.
        line (int): line number where the definition occurs.
        config_path (str): template definition file path.
        """
        print("ADLSJFA", line, config_path)
        super().__init__
        (
            f"Could not find a definition for tag {name}",
            line, config_path
        )


class UnknownDataTypeError(HyperConfError):
    """Signal an unsupported hyperconf data type."""

    def __init__(self, type_name: str, line: int,
                 config_path: str = None):
        """Initialize an UnknownDataTypeError exception.

        Arguments:
        type_name (str): the unknown type name.
        """
        super().__init__
        (
            f"The data type {type_name} is not supported.",
            line, config_path
        )


class UnkownOptionError(HyperConfError):
    """Signal an unknown argument for a config object."""

    def __init__(self, object_name: str, arg_name: str):
        """Initialize an UnkownOptionError exception.

        Arguments:
        object_name (str): configuration object name.
        opt_name (str): option name.
        """
        super().__init__
        (
            f"The object {object_name} does not support "
            f"option {arg_name}."
        )


class ConfigurationError(HyperConfError):
    """Thrown when an YAML configuration file cannot be loaded."""

    def __init__(self, message,
                 line: int,
                 config_path: str = None):
        """Initialize an InvalidYamlError.

        Args:
        message (str): the error message.
        """
        super().__init__(message, line, config_path)
