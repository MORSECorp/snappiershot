""" Serializer (and Deserializer) classes for the JSON format. """
import datetime
import json
from numbers import Number
from typing import Any, Collection, Dict

from .constants import (
    COLLECTION_TYPES,
    DATETIME_TYPES,
    PANDAS_TYPES,
    CustomEncodedCollectionTypes,
    CustomEncodedDatetimeTypes,
    CustomEncodedNumericTypes,
    CustomEncodedPandasTypes,
    JsonType,
    get_pandas,
)


class JsonSerializer(json.JSONEncoder):
    """ Custom JSON serializer.

    Examples:
        >>> import json
        >>> from snappiershot.serializers.json import JsonSerializer
        >>> data = {"a": 1, "b": 2}
        >>> assert json.dumps(data, cls=JsonSerializer) == '{"a": 1, "b": 2}'
    """

    def encode(self, obj: Any) -> str:
        """
        Override JSONEncoder.encode to support tuple type hinting.

        The default JSONEncoder supports both primitive types: tuples and lists. In its implementation,
         tuples are implicitly converted to lists. To avoid this, this method allows tuples and lists
         to be encoded as separate types.

        This method is intended to be called only by the ``json.dumps`` method.
        """

        def hint_tuples(obj_: Any) -> Any:
            """ Convert tuples in a pre-processing step.

            Extrapolated from: https://stackoverflow.com/a/15721641
            """
            if isinstance(obj_, list):
                return [hint_tuples(item) for item in obj_]
            if isinstance(obj_, COLLECTION_TYPES):
                # Collection encoded before recursion to support sets.
                return hint_tuples(self.encode_collection(obj_))
            if isinstance(obj_, dict):
                return {key: hint_tuples(value) for key, value in obj_.items()}
            return obj_

        return super().encode(hint_tuples(obj))

    def default(self, value: Any) -> Any:
        """ Encode a value into a serializable object.

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

        if self._is_pandas_object(value):
            return self.encode_pandas(value)

        raise NotImplementedError(  # pragma: no cover
            f"Encoding for this object is not yet implemented: {value} ({type(value)})"
        )

    @staticmethod
    def _is_pandas_object(obj: object) -> bool:
        """Return true if the given object is a pandas object

        A special effort is made to avoid importing pandas unless it's really necessary.
        """
        pd = get_pandas()
        if pd is not None:
            return isinstance(obj, PANDAS_TYPES)
        return False

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
        The values for the NUMERIC_KEY and NUMERIC_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedNumericTypes` class.

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

    @staticmethod
    def encode_collection(value: Collection) -> JsonType:
        """ Encoding for collection types.

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
        raise NotImplementedError(
            f"No encoding implemented for the following collection type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_pandas(value: Any) -> JsonType:
        """ Encoding for collection types.

        The custom encoding follows the template:
            {
              PANDAS_KEY: <type, as a string>>,
              PANDAS_VALUE_KEY: <value, with a list or dict-of-lists with (index, value) tuples>
            }

        The values for the PANDAS_KEY and PANDAS_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedPandasTypes` class.

        Raises:
            NotImplementedError - If encoding is not implemented for the given pandas type.
        """
        # A special effort is made to avoid importing pandas unless it's really necessary.
        import pandas as pd

        if isinstance(value, pd.DataFrame):
            encoded_value = value.to_dict("split")
            return CustomEncodedPandasTypes.dataframe.json_encoding(encoded_value)

        if isinstance(value, pd.Series):
            encoded_value = {
                "data": value.to_list(),
                "index": value.index.to_list(),
            }
            return CustomEncodedPandasTypes.series.json_encoding(encoded_value)

        raise NotImplementedError(
            f"No encoding implemented for the following pandas type: {value} ({type(value)})"
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

        if set(dct.keys()) == CustomEncodedCollectionTypes.keys():
            return self.decode_collection(dct)

        if set(dct.keys()) == CustomEncodedPandasTypes.keys():
            return self.decode_pandas(dct)

        return dct

    @staticmethod
    def decode_numeric(dct: Dict[str, Any]) -> Any:
        """ Decode an encoded numeric type.

        This encoded numeric type object must be of the form:
            {
              NUMERIC_KEY: <type-as-a-string>,
              NUMERIC_VALUE_KEY: <value>
            }
        The values for the NUMERIC_KEY and NUMERIC_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedNumericTypes` class.

        Raises:
            NotImplementedError - If decoding is not implement for the given numeric type.
        """
        type_name = dct.get(CustomEncodedNumericTypes.type_key)
        value = dct[CustomEncodedNumericTypes.complex.value_key]

        if type_name == CustomEncodedNumericTypes.complex.name:
            real, imag = value
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
        The values for the DATETIME_KEY and DATETIME_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedDatetimeTypes` class.

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

    @staticmethod
    def decode_collection(dct: Dict[str, Any]) -> Collection:
        """ Decode an encoded collection type.

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
            NotImplementedError - If decoding is not implement for the given numeric type.
        """
        type_name = dct.get(CustomEncodedCollectionTypes.type_key)
        values = dct.get(CustomEncodedCollectionTypes.value_key)

        if type_name == CustomEncodedCollectionTypes.set.name:
            return set(values)

        if type_name == CustomEncodedCollectionTypes.tuple.name:
            return tuple(values)

        raise NotImplementedError(
            f"Deserialization for the following collection type not implemented: {dct}"
        )

    @staticmethod
    def decode_pandas(dct: Dict[str, Any]) -> Collection:
        """ Decode an encoded pandas type.

        This encoded numeric type object must be of the form:
            {
              PANDAS_KEY: <type-as-a-string>,
              PANDAS_VALUE_KEY: [<values>]
            }
        The values for the PANDAS_KEY and PANDAS_VALUE_KEY constants are attributes
          to the `snappiershot.serializers.constants.CustomEncodedPandasTypes` class.

        Args:
            dct: dictionary to decode

        Returns:
            Decoded pandas object.

        Raises:
            NotImplementedError - If decoding is not implement for the given numeric type.
        """
        # A special effort is made to avoid importing pandas unless it's really necessary.
        import pandas as pd

        type_name = dct.get(CustomEncodedPandasTypes.type_key)
        value = dct.get(CustomEncodedPandasTypes.value_key)

        if type_name == CustomEncodedPandasTypes.dataframe.name:
            return pd.DataFrame(**value)

        if type_name == CustomEncodedPandasTypes.series.name:
            return pd.Series(**value)

        raise NotImplementedError(
            f"Deserialization for the following pandas type not implemented: {dct}"
        )
