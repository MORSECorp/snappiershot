""" Serializer (and Deserializer) class for the JSON format. """
import json
from numbers import Number
from collections.abc import Sequence
from typing import Any, Dict, Union

# Key identifying encoding of custom numeric types.
NUMERIC_KEY = "__snappiershot_numeric__"
NUMERIC_VALUE_KEY = "value"

# Key identifying encoding of sequence types.
SEQUENCE_KEY = "__snappiershot_sequence__"
SEQUENCE_VALUE_KEY = "values"

# The name identifying the numeric type encoding for complex types.
COMPLEX_TYPE = "complex"


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
        elif isinstance(value, Sequence):
            return self.encode_sequence(value)
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
            return {}
        if isinstance(value, complex):
            return {NUMERIC_KEY: COMPLEX_TYPE, NUMERIC_VALUE_KEY: [value.real, value.imag]}
        raise NotImplementedError(
            f"No encoding implemented for the following numeric type: {value} ({type(value)})"
        )

    @staticmethod
    def encode_sequence(value: Sequence) -> Union[Number, Dict[str, Any]]:
        """ Encoding for sequence types.

        This will recursively encode sequence data types, including lists, sets, and tuples.
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
        if isinstance(value, (list, set, tuple, range)):
            # These types are by default supported by the JSONEncoder base class.
            return {SEQUENCE_KEY: type(value), SEQUENCE_VALUE_KEY: }
        if isinstance(value, complex):
            return {NUMERIC_KEY: COMPLEX_TYPE, NUMERIC_VALUE_KEY: [value.real, value.imag]}
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
        if (NUMERIC_KEY in dct) and (NUMERIC_VALUE_KEY in dct):
            return self.decode_numeric(dct)
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
