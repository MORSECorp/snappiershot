""" Tests for snappiershot/serializers/json.py """
import datetime
import json
import pathlib
from decimal import Decimal
from math import inf, isnan, nan

import pytest
from pint import Unit
from snappiershot.serializers.constants import (
    CustomEncodedCollectionTypes,
    CustomEncodedDatetimeTypes,
    CustomEncodedNumericTypes,
    CustomEncodedPathTypes,
    CustomEncodedUnitTypes,
)
from snappiershot.serializers.json import JsonDeserializer, JsonSerializer


class TestNumericEncoding:
    """ Tests for custom encoding of numeric types. """

    NUMERIC_DECODING_TEST_CASES = [
        (3 + 4j, CustomEncodedNumericTypes.complex.json_encoding([3, 4])),
        (
            Decimal(3.1415),
            CustomEncodedNumericTypes.decimal.json_encoding(
                Decimal(3.1415).as_tuple()._asdict()
            ),
        ),
        (
            Decimal("3.1415"),
            CustomEncodedNumericTypes.decimal.json_encoding(
                Decimal("3.1415").as_tuple()._asdict()
            ),
        ),
    ]

    NUMERIC_ENCODING_TEST_CASES = [
        (12, 12),
        (3.14, 3.14),
        (inf, inf),
        (nan, nan),
    ] + NUMERIC_DECODING_TEST_CASES

    @staticmethod
    @pytest.mark.parametrize("value, expected", NUMERIC_ENCODING_TEST_CASES)
    def test_encode_numeric(value, expected):
        """ Test that the JsonSerializer.encode_numeric encodes values as expected. """
        # Arrange

        # Act
        result = JsonSerializer.encode_numeric(value)

        # Assert
        assert (result == expected) or (isnan(result) and isnan(expected))

    @staticmethod
    def test_encode_numeric_error():
        """ Test that the JsonSerializer.encode_numeric raises an error if no encoding is defined. """
        # Arrange
        value = "3.121"

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonSerializer.encode_numeric(value)

    @staticmethod
    @pytest.mark.parametrize("expected, value", NUMERIC_DECODING_TEST_CASES)
    def test_decode_numeric(expected, value):
        """ Test that the JsonDeserializer.decode_numeric decodes values as expected. """
        # Arrange

        # Act
        result = JsonDeserializer.decode_numeric(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_decode_numeric_error():
        """ Test that the JsonDeserializer.decode_numeric raises an error if no decoding is defined. """
        # Arrange
        value = {"numeric": "decimal", "value": "3.14"}

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonDeserializer.decode_numeric(value)


class TestDatetimeEncoding:
    """ Tests for custom encoding of datetime types. """

    DATETIME_DECODING_TEST_CASES = [
        # fmt: off
        (datetime.datetime(2020, 8, 9, 10, 11, 12, 13),
         CustomEncodedDatetimeTypes.datetime_without_timezone.json_encoding("2020-08-09T10:11:12.000013")),
        (datetime.datetime(2020, 8, 9, 10, 11, 12, 13, tzinfo=datetime.timezone.utc),
         CustomEncodedDatetimeTypes.datetime_with_timezone.json_encoding("2020-08-09T10:11:12.000013+0000")),
        (datetime.date(2020, 8, 9),
         CustomEncodedDatetimeTypes.date.json_encoding("2020-08-09")),
        (datetime.time(10, 11, 12, 13),
         CustomEncodedDatetimeTypes.time.json_encoding("10:11:12.000013")),
        (datetime.timedelta(seconds=12, microseconds=13),
         CustomEncodedDatetimeTypes.timedelta.json_encoding(12.000013)),
        # fmt: on
    ]

    DATETIME_ENCODING_TEST_CASES = DATETIME_DECODING_TEST_CASES

    @staticmethod
    @pytest.mark.parametrize("value, expected", DATETIME_ENCODING_TEST_CASES)
    def test_encode_datetime(value, expected):
        """ Test that the JsonSerializer.encode_datetime encodes values as expected. """
        # Arrange

        # Act
        result = JsonSerializer.encode_datetime(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_datetime_error():
        """ Test that the JsonSerializer.encode_datetime raises an error if no encoding is defined. """
        # Arrange
        value = "not a datetime"

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonSerializer.encode_datetime(value)

    @staticmethod
    @pytest.mark.parametrize("expected, value", DATETIME_DECODING_TEST_CASES)
    def test_decode_datetime(value, expected):
        """ Test that the JsonDeserializer.decode_datetime decodes values as expected. """
        # Arrange

        # Act
        result = JsonDeserializer.decode_datetime(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_decode_datetime_error():
        """ Test that the JsonDeserializer.decode_datetime raises an error if no decoding is defined. """
        # Arrange
        value = {"foo": "bar"}

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonDeserializer.decode_datetime(value)


class TestCollectionEncoding:
    """ Tests for custom encoding of collection types. """

    COLLECTION_DECODING_TEST_CASES = [
        ({1, 2, 3}, CustomEncodedCollectionTypes.set.json_encoding([1, 2, 3])),
        ((1, 2, 3), CustomEncodedCollectionTypes.tuple.json_encoding([1, 2, 3])),
        (b"\x01\x02\x03", CustomEncodedCollectionTypes.bytes.json_encoding([1, 2, 3]),),
    ]

    COLLECTION_ENCODING_TEST_CASES = [
        ("balloons are awesome", "balloons are awesome"),
        ([2, 4, 6, 8], [2, 4, 6, 8]),
    ] + COLLECTION_DECODING_TEST_CASES

    @staticmethod
    def test_encode_collection_error():
        """ Test that the JsonSerializer.encode_collection raises an error if no encoding is defined. """
        # Arrange
        value = bytearray(10)

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonSerializer.encode_collection(value)

    @staticmethod
    @pytest.mark.parametrize("value, expected", COLLECTION_ENCODING_TEST_CASES)
    def test_encode_collection(value, expected):
        """ Test that the JsonSerializer.encode_collection encodes values as expected. """
        # Arrange

        # Act
        result = JsonSerializer.encode_collection(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize("expected, value", COLLECTION_DECODING_TEST_CASES)
    def test_decode_collection(value, expected):
        """ Test that the JsonDeserializer.decode_collection decodes collections as expected. """
        # Arrange

        # Act
        result = JsonDeserializer.decode_collection(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_decode_collection_error():
        """ Test that the JsonDeserializer.decode_collection raises an error if no decoding is defined. """
        # Arrange
        value = {"foo": "bar"}

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonDeserializer.decode_collection(value)


class TestPathEncoding:
    """ Tests for custom encoding of Path types. """

    PATH_DECODING_TEST_CASES = [
        (
            pathlib.Path("/Users/"),
            CustomEncodedPathTypes.path.json_encoding(["/", "Users"]),
        ),
        (
            pathlib.PosixPath("/Users/Shared/"),
            CustomEncodedPathTypes.path.json_encoding(["/", "Users", "Shared"]),
        ),
        (
            pathlib.PurePosixPath("/Users/Shared/test"),
            CustomEncodedPathTypes.pure_posix_path.json_encoding(
                ["/", "Users", "Shared", "test"]
            ),
        ),
        (
            pathlib.PurePosixPath("/Users/guest/Documents/test"),
            CustomEncodedPathTypes.pure_posix_path.json_encoding(
                ["/", "Users", "guest", "Documents", "test"]
            ),
        ),
        (
            pathlib.PureWindowsPath("/Users/guest/Documents/test"),
            CustomEncodedPathTypes.pure_windows_path.json_encoding(
                ["\\", "Users", "guest", "Documents", "test"]
            ),
        ),
        (
            pathlib.PureWindowsPath("/Library/directory_name/sub_dir_name/test"),
            CustomEncodedPathTypes.pure_windows_path.json_encoding(
                ["\\", "Library", "directory_name", "sub_dir_name", "test"]
            ),
        ),
    ]

    PATH_ENCODING_TEST_CASES = PATH_DECODING_TEST_CASES

    PATH_ENCODING_UNSUPPORTED_CASES = [pathlib.PurePath, pathlib.WindowsPath, pathlib.Path]

    @staticmethod
    @pytest.mark.parametrize("value", PATH_ENCODING_UNSUPPORTED_CASES)
    def test_encode_path_error(value):
        """ Test that the JsonSerializer.encode_path raises an error if no encoding is defined. """
        # Arrange
        value = b"foobar"

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonSerializer.encode_path(value)

    @staticmethod
    @pytest.mark.parametrize("value, expected", PATH_ENCODING_TEST_CASES)
    def test_encode_path(value, expected):
        """ Test that the JsonSerializer.encode_path encodes values as expected. """
        # Arrange

        # Act
        result = JsonSerializer.encode_path(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize("expected, value", PATH_DECODING_TEST_CASES)
    def test_decode_path(value, expected):
        """ Test that the JsonDeserializer.decode_path decodes collections as expected. """
        # Arrange

        # Act
        result = JsonDeserializer.decode_path(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_decode_path_error():
        """ Test that the JsonDeserializer.decode_path raises an error if no decoding is defined. """
        # Arrange
        value = {"foo": "bar"}

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonDeserializer.decode_path(value)


class TestUnitEncoding:
    """ Tests for custom encoding of Unit types from pint. """

    UNIT_DECODING_TEST_CASES = [
        (Unit("meter"), CustomEncodedUnitTypes.unit.json_encoding("meter"),),
    ]

    UNIT_ENCODING_TEST_CASES = UNIT_DECODING_TEST_CASES

    @staticmethod
    def test_encode_unit_error():
        """ Test that the JsonSerializer.encode_unit raises an error if no encoding is defined. """
        # Arrange
        value = "foo"

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonSerializer.encode_unit(value)

    @staticmethod
    @pytest.mark.parametrize("value, expected", UNIT_ENCODING_TEST_CASES)
    def test_encode_unit(value, expected):
        """ Test that the JsonSerializer.encode_unit encodes values as expected. """
        # Arrange

        # Act
        result = JsonSerializer.encode_unit(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize("expected, value", UNIT_DECODING_TEST_CASES)
    def test_decode_unit(value, expected):
        """ Test that the JsonDeserializer.decode_unit decodes Units as expected. """
        # Arrange

        # Act
        result = JsonDeserializer.decode_unit(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_decode_unit_error():
        """ Test that the JsonDeserializer.decode_unit raises an error if no decoding is defined. """
        # Arrange
        value = {"foo": "bar"}

        # Act & Assert
        with pytest.raises(NotImplementedError):
            JsonDeserializer.decode_unit(value)


def test_round_trip(tmp_path: pathlib.Path):
    """ Test that a serialized and then deserialized dictionary is unchanged. """
    # Arrange
    data = {
        "bool": True,
        "none": None,
        "int": 12,
        "float": 3.14,
        "decimal_1": Decimal(3.1415),
        "decimal_2": Decimal("3.1415"),
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
        "path": pathlib.Path(),
        "pure_windows_path": pathlib.PureWindowsPath(),
        "pure_posix_Path": pathlib.PurePosixPath(),
        "bytes": b"bytes",
        "unit": Unit("meter"),
    }
    test_file = tmp_path / "test.json"

    # Act
    serialized = json.dumps(data, cls=JsonSerializer)
    deserialized = json.loads(serialized, cls=JsonDeserializer)

    json.dump(data, test_file.open("w"), cls=JsonSerializer)
    deserialized_from_file = json.load(test_file.open(), cls=JsonDeserializer)

    # Assert
    for key, value in deserialized.items():
        expected = data.get(key)
        assert expected == value
    assert deserialized == deserialized_from_file
