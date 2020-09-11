""" Serializer (and Deserializer) class for the JSON format. """
import json
from numbers import Number
from typing import Any, Dict, Union


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

        This method only gets called when the value is not-naturally serializable.
          (Naturally serializable objects are booleans, floats, strings, etc.)

        Any custom encoders must return a dictionary. This will allow them to
          be deserialized by the `snappiershot.serializers.json.JsonDeserializer`
          using object hooks.

        Args:
            value: The python object to encode.
        """
        if isinstance(value, Number):
            return self.encode_numeric(value)
        raise NotImplementedError(  # pragma: no cover
            f"Encoding for this object is not yet implemented: {value}"
        )

    @staticmethod
    def encode_numeric(value: Number) -> Union[Number, Dict[str, Any]]:
        """ Encoding for numeric types.

        This will do nothing to naturally serializable types (bool, int, float)
          but will perform custom serialization for non-supported types (complex).

        Raises:
            NotImplementedError - If encoding is not implement for the given numeric type.
        """
        if isinstance(value, (bool, int, float)):
            # These types are by default supported by the JSONEncoder base class.
            return value
        if isinstance(value, complex):
            return dict(numeric="complex", value=[value.real, value.imag])
        raise NotImplementedError(
            f"No encoding implemented for the following numeric type: {value}"
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
        if "numeric" in dct:
            return self.decode_numeric(dct)
        return dct

    @staticmethod
    def decode_numeric(dct: Dict[str, Any]) -> Any:
        """ Decode an encoded numeric type.

        This encoded numeric type object must be of the form:
            {
              "numeric": <type-as-a-string>,
              "value": <value>
            }

        Raises:
            NotImplementedError - If decoding is not implement for the given numeric type.
        """
        type_ = dct.get("numeric")
        if type_ == "complex":
            real, imag = dct["value"]
            return complex(real, imag)
        raise NotImplementedError(
            f"Deserialization for the following numerical type not implemented: {dct}"
        )
