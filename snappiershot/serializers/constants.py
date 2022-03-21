""" Constant values used by the serializers. """
import datetime
from abc import ABC
from decimal import Decimal
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Iterator, List, NamedTuple, Set, Union

from pint import Unit

_Primitive = Union[bool, float, int, None, str]
JsonType = Union[_Primitive, Dict[str, Any], List[Any]]


# noinspection PyUnresolvedReferences
class _CustomEncodedType(NamedTuple):
    """ Organizational object for holding information for serializing and de-serializing
    custom-encoded types.

    See the ``json_encoding` method for an example of how this information is used.

    Args:
        type_: The type object (constructor) for the type.
        name: The human-readable name for the type.
        type_key: The key used by snappiershot to declare the type when serialized.
        value_key: The key used for holding the value(s) of the serialized type.
        value_formatter: Optionally provided formatting string used to stringify data,
          i.e. datetime format strings.
    """

    type_: type
    name: str
    type_key: str
    value_key: str
    value_formatter: str = ""

    @property
    def type(self) -> type:
        """ Pass-through property to access the "type_" attribute. """
        return self.type_

    def json_encoding(self, encoded_value: JsonType) -> JsonType:
        """ Use the specified encoded value to create the JSON encoding.

        Args:
            encoded_value: An encoded value that is serializable into JSON.
        """
        return {self.type_key: self.name, self.value_key: encoded_value}


class _CustomEncodedTypeCollection(ABC):
    """ Abstract base class for CustomEncoded<group>Types classes.

    The _CustomEncodedTypes associated with the child classes are expected to
      be defined as class attributes. See:
        * `snappiershot.serializers.constants.CustomEncodedDatetimeTypes`
        * `snappiershot.serializers.constants.CustomEncodedNumericTypes`

    Additionally provided are the predefined ``list`` and ``keys`` classmethods.
    """

    # Corresponds to the _CustomEncodedType.type_key attribute.
    # Should be of the form __snappiershot_<name>__
    type_key: str

    # Corresponds to the _CustomEncodedType.value_key attribute.
    value_key: str

    @classmethod
    def list(cls) -> Iterator[_CustomEncodedType]:
        """ Returns an iterator of all _CustomEncodedType objects defined
        as class attributes.
        """
        return (
            value for value in vars(cls).values() if isinstance(value, _CustomEncodedType)
        )

    @classmethod
    def keys(cls) -> Set[str]:
        """ Returns a set of {type_key, value_key}. """
        return {cls.type_key, cls.value_key}


class CustomEncodedNumericTypes(_CustomEncodedTypeCollection):
    """ Collection of custom-encoded numeric types. """

    # Corresponds to the _CustomEncodedType.type_key attribute.
    type_key = "__snappiershot_numeric__"
    # Corresponds to the _CustomEncodedType.value_key attribute.
    value_key = "value"

    complex = _CustomEncodedType(
        type_=complex, name="complex", type_key=type_key, value_key=value_key
    )
    decimal = _CustomEncodedType(
        type_=Decimal, name="decimal", type_key=type_key, value_key=value_key
    )


class CustomEncodedDatetimeTypes(_CustomEncodedTypeCollection):
    """ Collection of custom-encoded datetime types. """

    # Corresponds to the _CustomEncodedType.type_key attribute.
    type_key = "__snappiershot_datetime__"
    # Corresponds to the _CustomEncodedType.value_key attribute.
    value_key = "value"

    date = _CustomEncodedType(
        type_=datetime.date,
        name="date",
        type_key=type_key,
        value_key=value_key,
        value_formatter="%Y-%m-%d",
    )
    datetime_with_timezone = _CustomEncodedType(
        type_=datetime.datetime,
        name="datetime_with_timezone",
        type_key=type_key,
        value_key=value_key,
        value_formatter="%Y-%m-%dT%H:%M:%S.%f%z",
    )
    datetime_without_timezone = _CustomEncodedType(
        type_=datetime.datetime,
        name="datetime_without_timezone",
        type_key=type_key,
        value_key=value_key,
        value_formatter="%Y-%m-%dT%H:%M:%S.%f",
    )
    time = _CustomEncodedType(
        type_=datetime.time,
        name="time",
        type_key=type_key,
        value_key=value_key,
        value_formatter="%H:%M:%S.%f",
    )
    timedelta = _CustomEncodedType(
        type_=datetime.timedelta, name="timedelta", type_key=type_key, value_key=value_key
    )


class CustomEncodedCollectionTypes(_CustomEncodedTypeCollection):
    """ Collection of custom-encoded collection types. """

    # Corresponds to the _CustomEncodedType.type_key attribute.
    type_key = "__snappiershot_collection__"
    # Corresponds to the _CustomEncodedType.value_key attribute.
    value_key = "values"

    set = _CustomEncodedType(type_=set, name="set", type_key=type_key, value_key=value_key)
    tuple = _CustomEncodedType(
        type_=tuple, name="tuple", type_key=type_key, value_key=value_key
    )
    bytes = _CustomEncodedType(
        type_=bytes, name="bytes", type_key=type_key, value_key=value_key
    )


class _UnavailableType:
    """ Empty class for handling optional type dependencies that are unavailable """


class CustomEncodedPathTypes(_CustomEncodedTypeCollection):
    """ Collection of custom-encoded Path types. """

    # Corresponds to the _CustomEncodedType.type_key attribute.
    type_key = "__snappiershot_path__"
    # Corresponds to the _CustomEncodedType.value_key attribute.
    value_key = "parts"

    path = _CustomEncodedType(
        type_=Path, name="Path", type_key=type_key, value_key=value_key
    )
    pure_posix_path = _CustomEncodedType(
        type_=PurePosixPath, name="PurePosixPath", type_key=type_key, value_key=value_key
    )
    pure_windows_path = _CustomEncodedType(
        type_=PureWindowsPath,
        name="PureWindowsPath",
        type_key=type_key,
        value_key=value_key,
    )


class CustomEncodedUnitTypes(_CustomEncodedTypeCollection):
    """ Collection of custom-encoded Unit types from the pint package. """

    # Corresponds to the _CustomEncodedType.type_key attribute.
    type_key = "__snappiershot_unit__"
    # Corresponds to the _CustomEncodedType.value_key attribute.
    value_key = "value"

    unit = _CustomEncodedType(
        type_=Unit, name="Unit", type_key=type_key, value_key=value_key
    )


# Tuples of types intended to be used for isinstance checking.
PRIMITIVE_TYPES = bool, float, int, type(None), str
COLLECTION_TYPES = tuple(value.type for value in CustomEncodedCollectionTypes.list())
DATETIME_TYPES = tuple(value.type for value in CustomEncodedDatetimeTypes.list())
NUMERIC_TYPES = tuple(value.type for value in CustomEncodedNumericTypes.list())
PATH_TYPES = PurePosixPath, PureWindowsPath, Path
UNIT_TYPES = tuple(value.type for value in CustomEncodedUnitTypes.list())
SERIALIZABLE_TYPES = (
    PRIMITIVE_TYPES
    + COLLECTION_TYPES
    + DATETIME_TYPES
    + NUMERIC_TYPES
    + PATH_TYPES
    + UNIT_TYPES
)
