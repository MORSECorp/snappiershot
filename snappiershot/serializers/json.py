""" Serializer (and Deserializer) class for the JSON format. """
import datetime
import json
from numbers import Number
from typing import Any, Dict

from .constants import (
    DATETIME_TYPES,
    CustomEncodedDatetimeTypes,
    CustomEncodedNumericTypes,
    JsonType,
)


class JsonSerializer(json.JSONEncoder):
    """ Custom JSON serializer.

    Examples:
        >>> import json
        >>> from snappiershot.serializers.json import JsonSerializer
        >>> data = {"a": 1, "b": 2}
        >>> assert json.dumps(data, cls=JsonSerializer) == '{"a": 1, "b": 2}'
    """

    def default(self, value: Any) -> Any:
        """ Encode a value into a serializable object.

        This method only gets called when the value is not naturally-serializable.
          (Naturally serializable objects are booleans, floats, strings, etc.)
          See: https://docs.python.org/3/library/json.html#py-to-json-table

        Any custom encoders must return a dictionary. This will allow them to
          be deserialized by the `snappiershot.serializers.json.JsonDeserializer`
          using object hooks.

        Args:
            value: The python object to encode.
        """
        if isinstance(value, Number):
            return self.encode_numeric(value)

        if isinstance(value, DATETIME_TYPES):
            return self.encode_datetime(value)

        raise NotImplementedError(  # pragma: no cover
            f"Encoding for this object is not yet implemented: {value} ({type(value)})"
        )

    @staticmethod
    def encode_numeric(value: Number) -> JsonType:
        """ Encoding for numeric types.

        This will do nothing to naturally serializable types (bool, int, float)
          but will perform custom encoding for non-supported types (complex).
        The custom encoding follows the template:
            {
              NUMERIC_KEY: <type-as-a-string>,
              NUMERIC_VALUE_KEY: <value>
            }
        The values for the NUMERIC_KEY and NUMERIC_VALUE_KEY constants can be found
          at the top of this file.

        Raises:
            NotImplementedError - If encoding is not implement for the given numeric type.
        """
        if isinstance(value, (bool, int, float)):
            # These types are by default supported by the JSONEncoder base class.
            return value
        if isinstance(value, complex):
            encoded_value = [value.real, value.imag]
            return CustomEncodedNumericTypes.complex.json_encoding(encoded_value)
        raise NotImplementedError(
            f"No encoding implemented for the following numeric type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_datetime(value: Any) -> JsonType:
        """ Encoding for datetime types

        This will perform custom encoding for datetime types

        The custom encoding follows the template:
            {
                DATETIME_KEY: <type-as-a-string>,
                DATETIME_VALUE_KEY: <value>
            }

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
            NotImplementedError - If encoding is not implement for the given numeric type.
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


class JsonDeserializer(json.JSONDecoder):
    """ Custom JSON deserializer.

    Examples:
        >>> import json
        >>> from snappiershot.serializers.json import JsonDeserializer
        >>> data = '{"a": 1, "b": 2}'
        >>> assert json.loads(data, cls=JsonDeserializer) == {"a": 1, "b": 2}
    """

    def __init__(self, **kwargs: Any):
        """ Hooks into the __init__ method of json.JSONDecoder.

        This is only expected to be called by the `json.loads` method.
        """
        super().__init__(object_hook=self.object_hook, **kwargs)

    def object_hook(self, dct: Dict[str, Any]) -> Any:
        """ Decodes the dictionary into an object.

        Custom decoding is done here, for the custom encodings that occurred within
          the `snappiershot.serializers.json.JsonSerializer.default` method.
        """
        if set(dct.keys()) == CustomEncodedNumericTypes.keys():
            return self.decode_numeric(dct)

        if set(dct.keys()) == CustomEncodedDatetimeTypes.keys():
            return self.decode_datetime(dct)

        return dct

    @staticmethod
    def decode_numeric(dct: Dict[str, Any]) -> Any:
        """ Decode an encoded numeric type.

        This encoded numeric type object must be of the form:
            {
              NUMERIC_KEY: <type-as-a-string>,
              NUMERIC_VALUE_KEY: <value>
            }
        The values for the NUMERIC_KEY and NUMERIC_VALUE_KEY constants can be found
          at the top of this file.

        Raises:
            NotImplementedError - If decoding is not implement for the given numeric type.
        """
        type_name = dct.get(CustomEncodedNumericTypes.type_key)
        value = dct[CustomEncodedNumericTypes.complex.value_key]

        if type_name == CustomEncodedNumericTypes.complex.name:
            real, imag = value
            return CustomEncodedNumericTypes.complex.type(real, imag)

        raise NotImplementedError(
            f"Deserialization for the following numerical type not implemented: {dct}"
        )

    @staticmethod
    def decode_datetime(dct: Dict[str, Any]) -> Any:
        """ Decode an encoded datetime type

        This encoded numeric type object must be of the form:
            {
              DATETIME_KEY: <type-as-a-string>,
              DATETIME_VALUE_KEY: <value>
            }
        The values for the DATETIME_KEY and DATETIME_VALUE_KEY constants can be found
          at the top of this file.

        Args:
            dct: dictionary to decode

        Returns:
            decoded datetime object, either a datetime.date, datetime.time, datetime.datetime, or datetime.timedelta

        Raises:
            NotImplementedError - If decoding is not implement for the given numeric type.
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
