""" Tests for snappiershot/serializers/json.py """
import datetime
import json
from decimal import Decimal
from math import inf, isnan, nan

import pytest
from snappiershot.serializers.json import (
    COMPLEX_TYPE,
    DATETIME_KEY,
    DATETIME_VALUE_KEY,
    NUMERIC_KEY,
    NUMERIC_VALUE_KEY,
    SEQUENCE_KEY,
    SEQUENCE_VALUE_KEY,
    DatetimeType,
    JsonDeserializer,
    JsonSerializer,
)

DATETIME_ENCODING_TEST_CASES = [
    (
        datetime.datetime(2020, 8, 9, 10, 11, 12, 13),
        {
            DATETIME_KEY: DatetimeType.DATETIME_WITHOUT_TZ.value,
            DATETIME_VALUE_KEY: "2020-08-09T10:11:12.000013",
        },
    ),
    (
        datetime.datetime(2020, 8, 9, 10, 11, 12, 13, tzinfo=datetime.timezone.utc),
        {
            DATETIME_KEY: DatetimeType.DATETIME_WITH_TZ.value,
            DATETIME_VALUE_KEY: "2020-08-09T10:11:12.000013+0000",
        },
    ),
    (
        datetime.date(2020, 8, 9),
        {DATETIME_KEY: DatetimeType.DATE.value, DATETIME_VALUE_KEY: "2020-08-09"},
    ),
    (
        datetime.time(10, 11, 12, 13),
        {DATETIME_KEY: DatetimeType.TIME.value, DATETIME_VALUE_KEY: "10:11:12.000013"},
    ),
    (
        datetime.timedelta(seconds=12, microseconds=13),
        {DATETIME_KEY: DatetimeType.TIMEDELTA.value, DATETIME_VALUE_KEY: 12.000013},
    ),
]

SEQUENCE_ENCODING_TEST_CASES = [
    ({1, 2, 3}, {SEQUENCE_KEY: "set", SEQUENCE_VALUE_KEY: [1, 2, 3]}),
    ((1, 2, 3), {SEQUENCE_KEY: "tuple", SEQUENCE_VALUE_KEY: [1, 2, 3]}),
]


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


@pytest.mark.parametrize("value, expected", DATETIME_ENCODING_TEST_CASES)
def test_encode_datetime(value, expected):
    """ Test that the JsonSerializer.encode_datetime encodes values as expected. """
    # Arrange

    # Act
    result = JsonSerializer.encode_datetime(value)

    # Assert
    assert result == expected


def test_encode_datetime_error():
    """ Test that the JsonSerializer.encode_datetime raises an error if no encoding is defined. """
    # Arrange
    value = "not a datetime"

    # Act & Assert
    with pytest.raises(NotImplementedError):
        JsonSerializer.encode_datetime(value)


@pytest.mark.parametrize("expected, value", DATETIME_ENCODING_TEST_CASES)
def test_decode_datetime(value, expected):
    """ Test that the JsonDeserializer.decode_datetime decodes values as expected. """
    # Arrange

    # Act
    result = JsonDeserializer.decode_datetime(value)

    # Assert
    assert result == expected


def test_decode_datetime_error():
    """ Test that the JsonDeserializer.decode_datetime raises an error if no decoding is defined. """
    # Arrange
    value = {"foo": "bar"}

    # Act & Assert
    with pytest.raises(NotImplementedError):
        JsonDeserializer.decode_datetime(value)


def test_encode_sequence_error():
    """ Test that the JsonSerializer.encode_sequence raises an error if no encoding is defined. """
    # Arrange
    value = b"banana"

    # Act & Assert
    with pytest.raises(NotImplementedError):
        js = JsonSerializer()
        js.encode_sequence(value)


@pytest.mark.parametrize(
    "value, expected", SEQUENCE_ENCODING_TEST_CASES + [([1, 2], [1, 2])]
)
def test_encode_sequence(value, expected):
    """ Test that the JsonSerializer.encode_sequence encodes values as expected. """
    # Arrange

    # Act
    js = JsonSerializer()
    result = js.encode_sequence(value)

    # Assert
    assert result == expected


@pytest.mark.parametrize("expected, value", SEQUENCE_ENCODING_TEST_CASES)
def test_decode_sequence(value, expected):
    """ Test that the JsonDeserializer.decode_sequence decodes sequences as expected. """
    # Arrange

    # Act
    jd = JsonDeserializer()
    result = jd.decode_sequence(value)

    # Assert
    assert result == expected


def test_decode_sequence_error():
    """ Test that the JsonDeserializer.decode_sequence raises an error if no decoding is defined. """
    # Arrange
    value = {"foo": "bar"}

    # Act & Assert
    with pytest.raises(NotImplementedError):
        jd = JsonDeserializer()
        jd.decode_sequence(value)


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
        "date": datetime.date(2020, 8, 9),
        "time": datetime.time(10, 11, 12, 13),
        "datetime_with_tz": datetime.datetime(
            2020, 8, 9, 10, 11, 12, 13, tzinfo=datetime.timezone.utc
        ),
        "datetime_without_tz": datetime.datetime(2020, 8, 9, 10, 11, 12, 13),
        "timedelta": datetime.timedelta(seconds=12, microseconds=13),
        "list": [1, 2, 3],
        "set": {1, 2, 3},
        "tuple": (1, 2, 3),
        "nested_list": [1, 2, [3, 4, []]],
        "nested_tuple": (1, 2, (3, 4, ())),
        "complex_list": [1, 2, (3, 4, {5})],
        "my_test": {(1, 2), (3, 4)},
        "my_test2": {"one", "two"},
    }

    # Act
    serialized = json.dumps(data, cls=JsonSerializer)
    deserialized = json.loads(serialized, cls=JsonDeserializer)

    # Assert
    assert deserialized == data
