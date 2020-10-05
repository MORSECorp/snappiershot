""" Serializer (and Deserializer) class for the JSON format. """
import datetime
import json
from enum import Enum
from numbers import Number
from typing import Any, Dict, Union
from copy import deepcopy

# Key identifying encoding of custom numeric types.
NUMERIC_KEY = "__snappiershot_numeric__"
NUMERIC_VALUE_KEY = "value"

# The name identifying the numeric type encoding for complex types.
COMPLEX_TYPE = "complex"

# Key identifying encoding of sequence types.
SEQUENCE_KEY = "__snappiershot_sequence__"
SEQUENCE_VALUE_KEY = "values"
SEQUENCE_TYPES = (set, list, tuple)


class SequenceType(Enum):
    SET = "set"
    LIST = "list"
    TUPLE = "tuple"


# Keys and values identifying encoding of datetime objects
DATETIME_KEY = "__snappiershot_datetime__"
DATETIME_VALUE_KEY = "value"
DATETIME_TYPES = (datetime.date, datetime.time, datetime.datetime, datetime.timedelta)


class DatetimeType(Enum):
    DATETIME_WITH_TZ = "datetime_with_timezone"
    DATETIME_WITHOUT_TZ = "datetime_without_timezone"
    DATE = "date"
    TIME = "time"
    TIMEDELTA = "timedelta"


class DatetimeFormatString(Enum):
    DATETIME_WITH_TZ = "%Y-%m-%dT%H:%M:%S.%f%z"
    DATETIME_WITHOUT_TZ = "%Y-%m-%dT%H:%M:%S.%f"
    DATE = "%Y-%m-%d"
    TIME = "%H:%M:%S.%f"


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

        if isinstance(value, SEQUENCE_TYPES):
            return self.encode_sequence(value)

        if isinstance(value, DATETIME_TYPES):
            return self.encode_datetime(value)

        raise NotImplementedError(  # pragma: no cover
            f"Encoding for this object is not yet implemented: {value} ({type(value)})"
        )

    @staticmethod
    def encode_numeric(value: Number) -> Union[Number, Dict[str, Any]]:
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
            return {NUMERIC_KEY: COMPLEX_TYPE, NUMERIC_VALUE_KEY: [value.real, value.imag]}
        raise NotImplementedError(
            f"No encoding implemented for the following numeric type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_datetime(value: Any) -> Dict[str, Any]:
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
        # because datetime.datetime objects are *also* instances of datetime.date (but not of datetime.time). E.g.:
        #   >> isinstance(datetime.datetime.now(), datetime.date)
        #   True
        #   >> isinstance(datetime.datetime.now(), datetime.time)
        #   False
        #   >> isinstance(datetime.datetime.now(), datetime.datetime)
        #   True

        if isinstance(value, datetime.datetime):
            if value.tzinfo is not None:
                # Encode as ISO 86001 format string with time zone information.
                return {
                    DATETIME_KEY: DatetimeType.DATETIME_WITH_TZ.value,
                    DATETIME_VALUE_KEY: value.strftime(
                        DatetimeFormatString.DATETIME_WITH_TZ.value
                    ),
                }

            else:
                # Encode as ISO 86001 format string without time zone information.
                return {
                    DATETIME_KEY: DatetimeType.DATETIME_WITHOUT_TZ.value,
                    DATETIME_VALUE_KEY: value.strftime(
                        DatetimeFormatString.DATETIME_WITHOUT_TZ.value
                    ),
                }

        if isinstance(value, datetime.date):
            # Encode as ISO 86001 format string
            return {
                DATETIME_KEY: DatetimeType.DATE.value,
                DATETIME_VALUE_KEY: value.strftime(DatetimeFormatString.DATE.value),
            }

        if isinstance(value, datetime.time):
            # Encode as ISO 86001 format string
            return {
                DATETIME_KEY: DatetimeType.TIME.value,
                DATETIME_VALUE_KEY: value.strftime(DatetimeFormatString.TIME.value),
            }

        if isinstance(value, datetime.timedelta):
            # Encode as total seconds, float (fractional part encodes microseconds)
            return {
                DATETIME_KEY: DatetimeType.TIMEDELTA.value,
                DATETIME_VALUE_KEY: value.total_seconds(),
            }

        raise NotImplementedError(
            f"No encoding implemented for the following datetime type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_sequence(value: Any) -> Union[Number, Dict[str, Any]]:
        """ Encoding for sequence types.

        This will recursively encode sequence data types, including lists, sets, and tuples.
        The custom encoding follows the template:
            {
              SEQUENCE_KEY: <type-as-a-string>,
              SEQUENCE_VALUE_KEY: [<value>]
            }
        The values for the SEQUENCE_KEY and SEQUENCE_VALUE_KEY constants can be found
          at the top of this file.

        Raises:
            NotImplementedError - If encoding is not implement for the given numeric type.
        """
        if isinstance(value, list):
            serializer = JsonSerializer()
            # These types are by default supported by the JSONEncoder base class.
            return {
                SEQUENCE_KEY: SequenceType.LIST.value,
                SEQUENCE_VALUE_KEY: [serializer.default(ele) for ele in list(value)],
            }
        if isinstance(value, set):
            serializer = JsonSerializer()
            # These types are by default supported by the JSONEncoder base class.
            return {
                SEQUENCE_KEY: SequenceType.SET.value,
                SEQUENCE_VALUE_KEY: [serializer.default(ele) for ele in list(value)],
            }
        if isinstance(value, tuple):
            serializer = JsonSerializer()
            # These types are by default supported by the JSONEncoder base class.
            return {
                SEQUENCE_KEY: SequenceType.TUPLE.value,
                SEQUENCE_VALUE_KEY: [serializer.default(ele) for ele in list(value)],
            }
        raise NotImplementedError(
            f"No encoding implemented for the following sequence type: {value} ({type(value)})"
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
        if set(dct.keys()) == {NUMERIC_KEY, NUMERIC_VALUE_KEY}:
            return self.decode_numeric(dct)

        if set(dct.keys()) == {DATETIME_KEY, DATETIME_VALUE_KEY}:
            return self.decode_datetime(dct)

        if set(dct.keys()) == {SEQUENCE_KEY, SEQUENCE_VALUE_KEY}:
            return self.decode_sequence(dct)

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
        type_ = dct.get(NUMERIC_KEY)
        if type_ == COMPLEX_TYPE:
            real, imag = dct[NUMERIC_VALUE_KEY]
            return complex(real, imag)
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
        type_ = dct.get(DATETIME_KEY)
        value = dct.get(DATETIME_VALUE_KEY)

        if type_ == DatetimeType.DATE.value:
            return datetime.datetime.strptime(value, DatetimeFormatString.DATE.value).date()

        if type_ == DatetimeType.TIME.value:
            # Value is ISO formatted time string
            return datetime.datetime.strptime(value, DatetimeFormatString.TIME.value).time()

        if type_ == DatetimeType.DATETIME_WITH_TZ.value:
            # Value is ISO formatted datetime string *with* timezone information
            return datetime.datetime.strptime(
                value, DatetimeFormatString.DATETIME_WITH_TZ.value
            )

        if type_ == DatetimeType.DATETIME_WITHOUT_TZ.value:
            # Value is ISO formatted datetime string *without* timezone information
            return datetime.datetime.strptime(
                value, DatetimeFormatString.DATETIME_WITHOUT_TZ.value
            )

        if type_ == DatetimeType.TIMEDELTA.value:
            # Value is total seconds, float
            return datetime.timedelta(seconds=value)

        raise NotImplementedError(
            f"Deserialization for the following datetime type not implemented: {dct}"
        )

    # @staticmethod
    # def traverse_dict(dct) -> Any:

    @staticmethod
    def decode_sequence(dct: Dict[str, Any]) -> Any:
        """ Decode an encoded sequence type

        This encoded numeric type object must be of the form:
            {
              SEQUENCE_KEY: <type-as-a-string>,
              SEQUENCE_VALUE_KEY: [<values>]
            }
        The values for the SEQUENCE_KEY and SEQUENCE_VALUE_KEY constants can be found
          at the top of this file.

        Args:
            dct: dictionary to decode

        Returns:
            decoded sequence object, either a set, list, or tuple

        Raises:
            NotImplementedError - If decoding is not implement for the given numeric type.
        """

        ds = JsonDeserializer()
        seq = []
        type_ = dct.get(SEQUENCE_KEY)
        value = dct.get(SEQUENCE_VALUE_KEY)

        if type_ not in [e.value for e in SequenceType]:
            raise NotImplementedError(
                f"Deserialization for the following sequence type not implemented: {dct}"
            )

        if type_ == SequenceType.LIST.value:
            tmp_seq = list()
            for e in value:
                if isinstance(e, dict) and SEQUENCE_KEY in e and SEQUENCE_VALUE_KEY in e:
                    tmp_seq.append(ds.decode_sequence(e))
                else:
                    tmp_seq.append(e)
            return seq + tmp_seq

        if type_ == SequenceType.SET.value:
            tmp_seq = list()
            for e in value:
                if isinstance(e, dict) and SEQUENCE_KEY in e and SEQUENCE_VALUE_KEY in e:
                    tmp_seq.append(ds.decode_sequence(e))
                else:
                    tmp_seq.append(e)
            return set(seq + tmp_seq)

        if type_ == SequenceType.TUPLE.value:
            tmp_seq = list()
            for e in value:
                if isinstance(e, dict) and SEQUENCE_KEY in e and SEQUENCE_VALUE_KEY in e:
                    tmp_seq.append(ds.decode_sequence(e))
                else:
                    tmp_seq.append(e)
            return tuple(seq + tmp_seq)
