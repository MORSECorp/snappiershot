""" Tests for snappiershot/serializers/json.py """
import json
from decimal import Decimal
from math import inf, isnan, nan

import pytest
from snappiershot.serializers.json import (
    COMPLEX_TYPE,
    NUMERIC_KEY,
    NUMERIC_VALUE_KEY,
    JsonDeserializer,
    JsonSerializer,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        (12, 12),
        (3.14, 3.14),
        (inf, inf),
        (nan, nan),
        (3 + 4j, {NUMERIC_KEY: COMPLEX_TYPE, NUMERIC_VALUE_KEY: [3, 4]}),
    ],
)
def test_encode_numeric(value, expected):
    """ Test that the JsonSerializer.encode_numeric encodes values as expected. """
    # Arrange

    # Act
    result = JsonSerializer.encode_numeric(value)

    # Assert
    assert (result == expected) or (isnan(result) and isnan(expected))


def test_encode_numeric_error():
    """ Test that the JsonSerializer.encode_numeric raises an error if no encoding is defined. """
    # Arrange
    value = Decimal("3.14")

    # Act & Assert
    with pytest.raises(NotImplementedError):
        JsonSerializer.encode_numeric(value)


@pytest.mark.parametrize(
    "value, expected", [({NUMERIC_KEY: COMPLEX_TYPE, NUMERIC_VALUE_KEY: [3, 4]}, 3 + 4j)]
)
def test_decode_numeric(value, expected):
    """ Test that the JsonDeserializer.decode_numeric decodes values as expected. """
    # Arrange

    # Act
    result = JsonDeserializer.decode_numeric(value)

    # Assert
    assert result == expected


def test_decode_numeric_error():
    """ Test that the JsonDeserializer.decode_numeric raises an error if no decoding is defined. """
    # Arrange
    value = {"numeric": "decimal", "value": "3.14"}

    # Act & Assert
    with pytest.raises(NotImplementedError):
        JsonDeserializer.decode_numeric(value)


def test_round_trip():
    """ Test that a serialized and then deserialized dictionary is unchanged. """
    # Arrange
    data = {
        "bool": True,
        "none": None,
        "int": 12,
        "float": 3.14,
        "inf": inf,
        "complex": 3 + 4j,
        "string": "string",
    }

    # Act
    serialized = json.dumps(data, cls=JsonSerializer)
    deserialized = json.loads(serialized, cls=JsonDeserializer)

    # Assert
    assert deserialized == data
