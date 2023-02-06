"""Supported template type definitions."""
import re

from enum import Enum
from abc import (
    ABC,
    abstractmethod
)

from hyperconf.errors import UnknownDataTypeError


class Keywords:
    """Define template syntactic keywords."""

    class Types(Enum):
        """Define supported data types."""

        STR = "str"
        INT = "int"
        FLOAT = "float"
        BOOL = "bool"
        LIST = "list"
        CLASS_NAME = "classname"

    class Template(Enum):
        """Define template-level keywords."""

        USE = "use"
        VERSION = "version"
        TYPE = "type"
        NAME = "name"
        DESCRIPTION = "description"
        REQUIRED = "required"
        ARGS = "args"

    class Parameter(Enum):
        """Define paramter definition keywords."""

        NAME = "name"
        TYPE = "type"
        DEFAULT_VALUE = "default-value"
        REQUIRED = "required"
        IS_PROPERTY = "is-property"


class hType(ABC):
    """Encapsulate value parsing and validation for a hyperconf type."""

    _supported_types = {}

    def __init__(self):
        """Initialize a htype."""
        hType._supported_types[self.name] = self

    @staticmethod
    def from_name(type_name):
        """Get a data type by name."""
        if type_name is None or not isinstance(type_name, str):
            raise ValueError("type_name must be string")

        if type_name in hType._supported_types:
            return hType._supported_types[type_name]
        else:
            list_match = hList._regex.match(type_name)
            if list_match:
                return hList(list_match.group(1))

            hclass_match = hClass._regex.match(type_name)
            if hclass_match:
                return hClass()

            raise UnknownDataTypeError(type_name)

    @staticmethod
    def is_supported(typename):
        """Return True if the typename is recognized."""
        if typename is None or not isinstance(typename, str):
            raise ValueError("typename must be string")

        if typename in hType._supported_types:
            return True

        list_match = hList._regex.match(typename)
        if list_match:
            return True

        return hClass._regex.match(typename)


    @abstractmethod
    def validate(self, value):
        """Provide value validation.

        Arguments:
        value (object): an object to validate.

        Returns:
        True if the value is convertible to type, False if not.

        """
        ...

    @abstractmethod
    def __call__(self, value):
        """Parse (convert) a value to this type.

        Arguments:
        value (object): object to convert.

        Returns:
        the converted value.
        """
        ...

    @property
    @abstractmethod
    def default_value(self):
        """Return the default value of the corresponding Python type."""
        ...


class hStr(hType):
    """Plain string type."""

    name = Keywords.Types.STR.value

    def __call__(self, value):
        """Return value as string."""
        if not self.validate(value):
            raise ValueError("not a string value")
        return str(value)

    def validate(self, value):
        """Accept any string value."""
        return isinstance(value, str)

    @property
    def default_value(self):
        """Return default str value."""
        return ""


class hBool(hType):
    """Boolean type."""

    name = Keywords.Types.BOOL.value

    def __call__(self, value):
        """Convert value to bool."""
        if isinstance(value, bool):
            return value
        if not self.validate(value):
            raise ValueError("not a boolean value")
        return value.lower() == "true"

    def validate(self, value):
        """Accept true/false values.

        The value can be a python bool type or the
        strings "true" or "false", case insensitive.
        """
        return isinstance(value, bool) or\
            str(value).lower() in ["true", "false"]

    @property
    def default_value(self):
        """Return default bool value."""
        return False


class hInt(hType):
    """An integer type."""

    name = Keywords.Types.INT.value

    def __init__(self):
        """Initialize a hint."""
        super().__init__()
        self._rf = re.compile(r"^[-+]?\d+$")

    def __call__(self, value):
        """Convert string to int."""
        if isinstance(value, int):
            return value
        if not self.validate(value):
            raise ValueError("not an integer value")
        return int(value)

    def validate(self, value):
        """Accept an python int value or an integer literal."""
        if not isinstance(value, str) and not isinstance(value, int):
            return False
        return not self._rf.match(value) is None

    @property
    def default_value(self):
        """Return default int value."""
        return 0


class hFloat(hType):
    """An integer type."""

    name = Keywords.Types.FLOAT.value

    def __init__(self):
        """Initialize a hfloat."""
        super().__init__()
        self._rf = re.compile(
            r"^[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?$"
        )

    def __call__(self, value):
        """Convert string to int."""
        if not self.validate(value):
            raise ValueError("not float value")
        return float(value)

    def validate(self, value):
        """Accept an python float value or float literal."""
        return isinstance(value, float) or\
            not self._rf.match(value) is None

    @property
    def default_value(self):
        """Return default float value."""
        return 0.0


class hList(hType):
    """Generic list type."""

    name = Keywords.Types.LIST.value
    _regex = re.compile(r"^list\[(\w+)\]$")

    def __init__(self, type_name):
        """Initialize a generic list type."""
        super().__init__()
        self._generic_type = hType.from_name(type_name)

    def __call__(self, value):
        """Convert a list literal to a python list, with validation."""
        if not self.validate(value):
            raise ValueError(f"not a {self.name} value")
        return [self._generic_type.__call__(_.strip())
                for _ in value.split(",")]

    def validate(self, value):
        """Validate value as a list literal."""
        return value is not None and isinstance(value, str) and\
            all([self._generic_type.validate(_.strip())
                 for _ in value.split(",")])

    @property
    def default_value(self):
        """Return empty list."""
        return []


class hClass(hType):
    """A python fully qualified type name."""

    name = Keywords.Types.CLASS_NAME.value
    _regex = re.compile(
        r"^([a-zA-Z_]+[a-zA-Z0-9_]*)(.[a-zA-Z0-9_]+[a-zA-Z0-9_]*)*$"
    )

    def __call__(self, value):
        """Validate value."""
        self.validate(value)
        return value

    def validate(self, value):
        """Validate a type name."""
        return value is not None and\
            isinstance(value, str) and\
            hClass._regex.match(value)

    @property
    def default_value(self):
        """Return empty string."""
        return ""


# Register types.
_ = [hStr(), hInt(), hBool(), hFloat(), hClass(),
     [hList(_.value) for _ in Keywords.Types]]
