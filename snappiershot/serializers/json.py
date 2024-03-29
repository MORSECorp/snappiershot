""" Serializer (and Deserializer) classes for the JSON format. """
import datetime
import json
from decimal import Decimal, DecimalTuple
from numbers import Number
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import Any, Collection, Dict, Iterator, List

from pint import Unit

from .constants import (
    COLLECTION_TYPES,
    DATETIME_TYPES,
    PATH_TYPES,
    UNIT_TYPES,
    CustomEncodedCollectionTypes,
    CustomEncodedDatetimeTypes,
    CustomEncodedNumericTypes,
    CustomEncodedPathTypes,
    CustomEncodedUnitTypes,
    JsonType,
)


class JsonSerializer(json.JSONEncoder):
    """Custom JSON serializer.

    Examples:
        >>> import json
        >>> from snappiershot.serializers.json import JsonSerializer
        >>> data = {"a": 1, "b": 2}
        >>> assert json.dumps(data, cls=JsonSerializer) == '{"a": 1, "b": 2}'
    """

    @classmethod
    def _hint_tuples(cls, obj: Any) -> Any:
        """Convert tuples in a pre-processing step.

        Extrapolated from: https://stackoverflow.com/a/15721641
        """
        if isinstance(obj, list):
            return [cls._hint_tuples(item) for item in obj]
        if isinstance(obj, COLLECTION_TYPES):
            # Collection encoded before recursion to support sets.
            return cls._hint_tuples(cls.encode_collection(obj))
        if isinstance(obj, dict):
            return {key: cls._hint_tuples(value) for key, value in obj.items()}
        return obj

    def encode(self, obj: Any) -> str:
        """
        Override JSONEncoder.encode to support tuple type hinting.

        The default JSONEncoder supports both primitive types: tuples and lists. In its implementation,
         tuples are implicitly converted to lists. To avoid this, this method allows tuples and lists
         to be encoded as separate types.

        This method is intended to be called only by the ``json.dumps`` method.
        """
        return super().encode(self._hint_tuples(obj))

    def iterencode(self, obj: Any, _one_shot: bool = False) -> Iterator[str]:
        """
        Override JSONEncoder.iterencode to support tuple type hinting.

        The default JSONEncoder supports both primitive types: tuples and lists. In its implementation,
         tuples are implicitly converted to lists. To avoid this, this method allows tuples and lists
         to be encoded as separate types.

        This method is intended to be called only by the ``json.dump`` method.
        """
        return super().iterencode(self._hint_tuples(obj), _one_shot)

    def default(self, value: Any) -> Any:
        """Encode a value into a serializable object.

        This method only gets called when the value is not naturally-serializable.
          (Naturally serializable objects are booleans, floats, strings, etc.)
          See: https://docs.python.org/3/library/json.html#py-to-json-table

        Any custom encoders must return a dictionary. This will allow them to
          be deserialized by the `snappiershot.serializers.json.JsonDeserializer`
          using object hooks.

        Encoding of collections (sets and tuples) are done in a pre-processing step
          within the ``JsonSerializer.encode`` method. That method should always be
          called prior to this method.

        Args:
            value: The python object to encode.
        """
        if isinstance(value, Number):
            return self.encode_numeric(value)

        if isinstance(value, DATETIME_TYPES):
            return self.encode_datetime(value)

        if isinstance(value, PATH_TYPES):
            return self.encode_path(value)

        if isinstance(value, UNIT_TYPES):
            return self.encode_unit(value)

        raise NotImplementedError(  # pragma: no cover
            f"Encoding for this object is not yet implemented: {value} ({type(value)})"
        )

    @staticmethod
    def encode_numeric(value: Number) -> JsonType:
        """Encoding for numeric types.

        This will do nothing to naturally serializable types (bool, int, float)
          but will perform custom encoding for non-supported types (complex).
        This will convert Decimal values to their tuple encodings.
            See: https://docs.python.org/3.9/library/decimal.html#decimal.Decimal.as_tuple
        The custom encoding follows the template:
            {
              NUMERIC_KEY: <type-as-a-string>,
              NUMERIC_VALUE_KEY: <value>
            }
        The values for the NUMERIC_KEY and NUMERIC_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedNumericTypes` class.

        Raises:
            NotImplementedError - If encoding is not implement for the given numeric type.
        """
        if isinstance(value, (bool, int, float)):
            # These types are by default supported by the JSONEncoder base class.
            return value
        if isinstance(value, complex):
            encoded_value: List[float] = [value.real, value.imag]
            return CustomEncodedNumericTypes.complex.json_encoding(encoded_value)
        if isinstance(value, Decimal):
            encode_value: Dict[str, Any] = value.as_tuple()._asdict()
            return CustomEncodedNumericTypes.decimal.json_encoding(encode_value)
        raise NotImplementedError(
            f"No encoding implemented for the following numeric type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_datetime(value: Any) -> JsonType:
        """Encoding for datetime types

        This will perform custom encoding for datetime types

        The custom encoding follows the template:
            {
                DATETIME_KEY: <type-as-a-string>,
                DATETIME_VALUE_KEY: <value>
            }

        The values for the DATETIME_KEY and DATETIME_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedDatetimeTypes` class.

        The different datetime types/values are encoded as:
            Type                            Value encoded as
            ----                            ----------------
            datetime.date                   ISO 8601 string
            datetime.time                   ISO 8601 string
            datetime.datetime (w/ TZ info)  ISO 8601 string with TZ info
            datetime.datetime (w/o TZ info) ISO 8601 string without TZ info
            datetime.timedelta              total seconds, float

        Args:
            value: datetime value to be encoded

        Returns:
            Dictionary with encoded datetime type and value

        Raises:
            NotImplementedError - If encoding is not implemented for the given datetime type.
        """

        # Note: the "datetime.datetime" check must be before the "datetime.date" check
        # because datetime.datetime objects are *also* instances of datetime.date
        # (but not of datetime.time). E.g.:
        #   >> isinstance(datetime.datetime.now(), datetime.date)
        #   True
        #   >> isinstance(datetime.datetime.now(), datetime.time)
        #   False
        #   >> isinstance(datetime.datetime.now(), datetime.datetime)
        #   True

        if isinstance(value, datetime.datetime):
            if value.tzinfo is not None:
                # Encode as ISO 86001 format string with time zone information.
                type_ = CustomEncodedDatetimeTypes.datetime_with_timezone
                return type_.json_encoding(value.strftime(type_.value_formatter))
            else:
                # Encode as ISO 86001 format string without time zone information.
                type_ = CustomEncodedDatetimeTypes.datetime_without_timezone
                return type_.json_encoding(value.strftime(type_.value_formatter))

        if isinstance(value, datetime.date):
            # Encode as ISO 86001 format string
            type_ = CustomEncodedDatetimeTypes.date
            return type_.json_encoding(value.strftime(type_.value_formatter))

        if isinstance(value, datetime.time):
            # Encode as ISO 86001 format string
            type_ = CustomEncodedDatetimeTypes.time
            return type_.json_encoding(value.strftime(type_.value_formatter))

        if isinstance(value, datetime.timedelta):
            # Encode as total seconds, float (fractional part encodes microseconds)
            type_ = CustomEncodedDatetimeTypes.timedelta
            return type_.json_encoding(value.total_seconds())

        raise NotImplementedError(
            f"No encoding implemented for the following datetime type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_collection(value: Collection) -> JsonType:
        """Encoding for collection types.

        The custom encoding follows the template:
            {
              COLLECTION_KEY: <type-as-a-string>,
              COLLECTION_VALUE_KEY: [<value>]
            }
        The values for the COLLECTION_KEY and COLLECTION_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedCollectionTypes` class.

        Raises:
            NotImplementedError - If encoding is not implemented for the given numeric type.
        """
        if isinstance(value, (str, list)):
            # These are automatically serialized by the ``json`` module.
            return value
        if isinstance(value, set):
            return CustomEncodedCollectionTypes.set.json_encoding(list(value))
        if isinstance(value, tuple):
            return CustomEncodedCollectionTypes.tuple.json_encoding(list(value))
        if isinstance(value, bytes):
            return CustomEncodedCollectionTypes.bytes.json_encoding(list(value))
        raise NotImplementedError(
            f"No encoding implemented for the following collection type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_path(value: PurePath) -> JsonType:
        """Encoding for Path types

        This will perform custom encoding for all Path types, as all Path types are subclasses of the PurePath type.
        Instances of the PurePath type are handled separately from instances of the Path type.

        The custom encoding follows the template:
            {
                PATH_KEY: <type-as-a-string>,
                PATH_VALUE_KEY: [<parts>]
            }

        The values for the PATH_KEY and PATH_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedPathTypes` class.

        Args:
            value: Path value to be encoded

        Returns:
            Dictionary with encoded Path type and parts

        Raises:
            NotImplementedError - If encoding is not implemented for the given Path type.
        """
        if isinstance(value, Path):
            encoded_value = list(value.parts)
            return CustomEncodedPathTypes.path.json_encoding(encoded_value)

        if isinstance(value, PureWindowsPath):
            encode_value = list(value.parts)
            return CustomEncodedPathTypes.pure_windows_path.json_encoding(encode_value)

        if isinstance(value, PurePosixPath):
            encode_value = list(value.parts)
            return CustomEncodedPathTypes.pure_posix_path.json_encoding(encode_value)

        raise NotImplementedError(
            f"No encoding implemented for the following Path type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_unit(value: Unit) -> JsonType:
        """Encoding for Unit types coming from the pint package

        The custom encoding follows the template:
            {
                UNIT_KEY: <type-as-a-string>,
                UNIT_VALUE_KEY: [<value>]
            }

        The values for the UNIT_KEY and UNIT_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedUnitTypes` class.

        Args:
            value: Unit value to be encoded

        Returns:
            Dictionary with encoded Unit and value

        Raises:
            NotImplementedError - If encoding is not implemented for the given Unit type.
        """
        if isinstance(value, Unit):
            encoded_value = str(value)
            return CustomEncodedUnitTypes.unit.json_encoding(encoded_value)

        raise NotImplementedError(
            f"No encoding implemented for the following Unit type: {value} ({type(value)})"
        )


class JsonDeserializer(json.JSONDecoder):
    """Custom JSON deserializer.

    Examples:
        >>> import json
        >>> from snappiershot.serializers.json import JsonDeserializer
        >>> data = '{"a": 1, "b": 2}'
        >>> assert json.loads(data, cls=JsonDeserializer) == {"a": 1, "b": 2}
    """

    def __init__(self, **kwargs: Any):
        """Hooks into the __init__ method of json.JSONDecoder.

        This is only expected to be called by the `json.loads` method.
        """
        super().__init__(object_hook=self.object_hook, **kwargs)

    def object_hook(self, dct: Dict[str, Any]) -> Any:
        """Decodes the dictionary into an object.

        Custom decoding is done here, for the custom encodings that occurred within
          the `snappiershot.serializers.json.JsonSerializer.default` method.
        """
        if set(dct.keys()) == CustomEncodedNumericTypes.keys():
            return self.decode_numeric(dct)

        if set(dct.keys()) == CustomEncodedDatetimeTypes.keys():
            return self.decode_datetime(dct)

        if set(dct.keys()) == CustomEncodedCollectionTypes.keys():
            return self.decode_collection(dct)

        if set(dct.keys()) == CustomEncodedPathTypes.keys():
            return self.decode_path(dct)

        if set(dct.keys()) == CustomEncodedUnitTypes.keys():
            return self.decode_unit(dct)

        return dct

    @staticmethod
    def decode_numeric(dct: Dict[str, Any]) -> Any:
        """Decode an encoded numeric type.

        This encoded numeric type object must be of the form:
            {
              NUMERIC_KEY: <type-as-a-string>,
              NUMERIC_VALUE_KEY: <value>
            }
        The values for the NUMERIC_KEY and NUMERIC_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedNumericTypes` class.
        Decimal types are decoded by reassembling the DecimalTuple which was cast to a
          list during the encoding process.
        Raises:
            NotImplementedError - If decoding is not implemented for the given numeric type.
        """
        type_name = dct.get(CustomEncodedNumericTypes.type_key)
        value = dct[CustomEncodedNumericTypes.complex.value_key]

        if type_name == CustomEncodedNumericTypes.complex.name:
            real, imag = value
            return complex(real, imag)
        if type_name == CustomEncodedNumericTypes.decimal.name:
            return Decimal(DecimalTuple(**value))

        raise NotImplementedError(
            f"Deserialization for the following numerical type not implemented: {dct}"
        )

    @staticmethod
    def decode_datetime(dct: Dict[str, Any]) -> Any:
        """Decode an encoded datetime type

        This encoded numeric type object must be of the form:
            {
              DATETIME_KEY: <type-as-a-string>,
              DATETIME_VALUE_KEY: <value>
            }
        The values for the DATETIME_KEY and DATETIME_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedDatetimeTypes` class.

        Args:
            dct: dictionary to decode

        Returns:
            decoded datetime object, either a datetime.date, datetime.time, datetime.datetime, or datetime.timedelta

        Raises:
            NotImplementedError - If decoding is not implemented for the given numeric type.
        """
        type_name = dct.get(CustomEncodedDatetimeTypes.type_key)
        value = dct.get(CustomEncodedDatetimeTypes.value_key)

        if type_name == CustomEncodedDatetimeTypes.date.name:
            # Value is ISO formatted date string.
            obj = CustomEncodedDatetimeTypes.date
            return datetime.datetime.strptime(value, obj.value_formatter).date()

        if type_name == CustomEncodedDatetimeTypes.time.name:
            # Value is ISO formatted time string.
            obj = CustomEncodedDatetimeTypes.time
            return datetime.datetime.strptime(value, obj.value_formatter).time()

        if type_name == CustomEncodedDatetimeTypes.datetime_with_timezone.name:
            # Value is ISO formatted datetime string *with* timezone information.
            obj = CustomEncodedDatetimeTypes.datetime_with_timezone
            return datetime.datetime.strptime(value, obj.value_formatter)

        if type_name == CustomEncodedDatetimeTypes.datetime_without_timezone.name:
            # Value is ISO formatted datetime string *without* timezone information.
            obj = CustomEncodedDatetimeTypes.datetime_without_timezone
            return datetime.datetime.strptime(value, obj.value_formatter)

        if type_name == CustomEncodedDatetimeTypes.timedelta.name:
            # Value is total seconds, float.
            return CustomEncodedDatetimeTypes.timedelta.type(seconds=value)

        raise NotImplementedError(
            f"Deserialization for the following datetime type not implemented: {dct}"
        )

    @staticmethod
    def decode_collection(dct: Dict[str, Any]) -> Collection:
        """Decode an encoded collection type.

        This encoded numeric type object must be of the form:
            {
              SEQUENCE_KEY: <type-as-a-string>,
              SEQUENCE_VALUE_KEY: [<values>]
            }
        The values for the COLLECTION_KEY and COLLECTION_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedCollectionTypes` class.

        Args:
            dct: dictionary to decode

        Returns:
            Decoded collection object.

        Raises:
            NotImplementedError - If decoding is not implemented for the given numeric type.
        """
        type_name = dct.get(CustomEncodedCollectionTypes.type_key)
        values = dct.get(CustomEncodedCollectionTypes.value_key)

        if type_name == CustomEncodedCollectionTypes.set.name:
            return set(values)

        if type_name == CustomEncodedCollectionTypes.tuple.name:
            return tuple(values)

        if type_name == CustomEncodedCollectionTypes.bytes.name:
            return bytes(values)

        raise NotImplementedError(
            f"Deserialization for the following collection type not implemented: {dct}"
        )

    @staticmethod
    def decode_path(dct: Dict[str, Any]) -> PurePath:
        """Decode an encoded Path type.

        This encoded Path type object must be of the form:
            {
              PATH_KEY: <type-as-a-string>,
              PATH_VALUE_KEY: [<parts>]
            }
        The values for the PATH_KEY and PATH_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedPathTypes` class.

        Path and PurePath types are decoded by reassembling the PurePath.parts tuple which was cast to a
          list during the encoding process.

        NOTE: WindowsPath, PosixPath, PurePath types are NOT currently supported.

            This is intentional, to avoid OS-specific pathlib errors such as snapshots being created on a
             Posix machine and tested on a Windows machine.
        Raises:
            NotImplementedError - If decoding is not implemented for the given Path type.
        """
        type_name = dct.get(CustomEncodedPathTypes.type_key)
        parts = dct.get(CustomEncodedPathTypes.value_key)

        if type_name == CustomEncodedPathTypes.path.name:
            return Path().joinpath(*parts)
        if type_name == CustomEncodedPathTypes.pure_posix_path.name:
            return PurePosixPath().joinpath(*parts)
        if type_name == CustomEncodedPathTypes.pure_windows_path.name:
            return PureWindowsPath().joinpath(*parts)

        raise NotImplementedError(
            f"Deserialization for the following Path type not implemented: {dct}"
        )

    @staticmethod
    def decode_unit(dct: Dict[str, Any]) -> str:
        """Decode an encoded Unit type from pint.

        This encoded Unit type object must be of the form:
            {
              UNIT_KEY: <type-as-a-string>,
              UNIT_VALUE_KEY: [<value>]
            }
        The values for the UNIT_KEY and UNIT_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedUnitTypes` class.

        Args:
            dct: dictionary to decode

        Returns:
            Decoded Unit object as a string due to inability to compare units of different registries.

        Raises:
            NotImplementedError - If decoding is not implemented for the given Unit type.
        """
        type_name = dct.get(CustomEncodedUnitTypes.type_key)
        value = dct.get(CustomEncodedUnitTypes.value_key)

        if type_name == CustomEncodedUnitTypes.unit.name:
            return value

        raise NotImplementedError(
            f"Deserialization for the following Unit type not implemented: {dct}"
        )
