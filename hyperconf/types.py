"""Supported template type definitions."""
import re
from abc import (
    ABC,
    abstractmethod
)

from hyperconf.errors import UnknownDataTypeError


class htype(ABC):
    """Encapsulate value parsing and validation for a hyperconf type."""

    _supported_types = {}

    def __init__(self, name):
        """Initialize a HType.

        Arguments:
        name (str): type name.
        """
        if name is None:
            raise ValueError("name is None")
        self._name = name

        htype._supported_types[self._name] = self

    @staticmethod
    def from_name(type_name):
        """Get a data type by name."""
        if type_name is None or not isinstance(type_name, str):
            raise ValueError("type_name must be string")

        if type_name not in htype._supported_types:
            raise UnknownDataTypeError(type_name)
        return htype._supported_types[type_name]

    @staticmethod
    def is_supported(typename):
        """Return True if the typename is recognized."""
        if typename is None or not isinstance(typename, str):
            raise ValueError("typename must be string")
        return typename in htype._supported_types

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
    def name(self):
        """Return type name."""
        return self._name


class hstr(htype):
    """Plain string type."""

    def __init__(self):
        """Initialize a HStr."""
        super().__init__("str")

    def validate(self, value):
        """Accept any string value."""
        return isinstance(value, str)

    def __call__(self, value):
        """Return value as string."""
        if not self.validate(value):
            raise ValueError("not a string value")
        return str(value)


class hbool(htype):
    """Boolean type."""

    def __init__(self):
        """Initialize a HBool type."""
        super().__init__("bool")

    def validate(self, value):
        """Accept true/false values.

        The value can be a python bool type or the
        strings "true" or "false", case insensitive.
        """
        return isinstance(value, bool) or\
            str(value).lower() in ["true", "false"]

    def __call__(self, value):
        """Convert value to bool."""
        if isinstance(value, bool):
            return value
        if not self.validate(value):
            raise ValueError("not a boolean value")
        return value.lower() == "true"


class hint(htype):
    """An integer type."""

    def __init__(self):
        """Initialize a hint."""
        super().__init__("int")
        self._rf = re.compile(r"^[-+]?\d+$")

    def validate(self, value):
        """Accept an python int value or an integer literal."""
        if not isinstance(value, str) and not isinstance(value, int):
            return False
        return not self._rf.match(value) is None

    def __call__(self, value):
        """Convert string to int."""
        if isinstance(value, int):
            return value
        if not self.validate(value):
            raise ValueError("not an integer value")
        return int(value)


class hfloat(htype):
    """An integer type."""

    def __init__(self):
        """Initialize a hfloat."""
        super().__init__("float")
        self._rf = re.compile(
            r"^[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?$"
        )

    def validate(self, value):
        """Accept an python float value or float literal."""
        return isinstance(value, float) or\
            not self._rf.match(value) is None

    def __call__(self, value):
        """Convert string to int."""
        if not self.validate(value):
            raise ValueError("not float value")
        return float(value)


class hlist(htype):
    """Generic list type."""

    def __init__(self, type_name):
        """Initialize a generic list type."""
        super().__init__(f"list[{type_name}]")
        self._generic_type = htype.from_name(type_name)

    def validate(self, value):
        """Validate value as a list literal."""
        return value is not None and isinstance(value, str) and\
            all([self._generic_type.validate(_.strip())
                 for _ in value.split(",")])

    def __call__(self, value):
        """Convert a list literal to a python list, with validation."""
        if not self.validate(value):
            raise ValueError(f"not a {self.name} value")
        return [self._generic_type.__call__(_.strip())
                for _ in value.split(",")]


# Register types.
_ = hstr(),\
    hint(),\
    hbool(),\
    hfloat(),\
    [hlist(_().name) for _ in [hstr, hint, hbool, hfloat]]
