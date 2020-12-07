""" Tests for snappiershot/serializers/utils.py """
from types import SimpleNamespace

import pandas as pd
import pytest
from snappiershot.serializers.utils import (
    default_encode_value,
    encode_exception,
    get_snapshot_file,
)


class TestDefaultEncodeValue:
    """ Tests for the default_encode_value utility function. """

    @staticmethod
    def test_encode_class():
        """ Test that a class is encoded as expected. """
        # Arrange
        value = SimpleNamespace(a=1, b="banana", c=None)
        expected = dict(a=1, b="banana", c=None)

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_class_recursive():
        """ Test that a class is recursively encoded as expected. """
        # Arrange
        value = SimpleNamespace(
            class_=SimpleNamespace(a=1, b="banana", c=None),
            dict_=dict(key_1="value_1", key_2="value_2"),
            list_=["item_1", "item_2"],
        )
        expected = dict(
            class_=dict(a=1, b="banana", c=None),
            dict_=dict(key_1="value_1", key_2="value_2"),
            list_=["item_1", "item_2"],
        )

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_custom_encoder():
        """ Test that a class that specifies a custom encoder
        gets encoded using that method.
        """
        # Arrange
        encoding = "CUSTOM ENCODING"

        class ClassWithCustomEncoder:
            """ Example class with custom encoder. """

            # noinspection PyMethodMayBeStatic
            def __snapshot__(self):
                """ Custom encoder for snappiershot. """
                return encoding

        value = ClassWithCustomEncoder()

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == encoding

    @staticmethod
    def test_encode_serializable_types():
        """ Test that a class with custom-encoded types does not encode these types. """
        # Arrange
        from datetime import datetime

        complex_value = 3 + 4j
        datetime_value = datetime(2020, 10, 8)
        value = SimpleNamespace(complex=complex_value, datetime=datetime_value)
        expected = dict(complex=complex_value, datetime=datetime_value)

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize("value", (set("abcdefg"), (1, 2, 3)))
    def test_encode_collection_types(value):
        """ Test that a class with custom-encoded types does not encode collection. """
        # Arrange

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == value

    @staticmethod
    @pytest.mark.parametrize("value", [isinstance, type, iter([1, 2])])
    def test_encode_unserializable(value):
        """ Test that an unserializable object raises an error. """
        # Arrange

        # Act & Assert
        with pytest.raises(ValueError):
            default_encode_value(value)

    @staticmethod
    def test_encode_unserializable_recurse():
        """ Test that a class with un-serializable attributes does not error. """
        # Arrange
        value = SimpleNamespace(
            class_=SimpleNamespace(good="class", bad=type),
            dict_=dict(good="dict", bad=dict),
            list_=["list", list],
        )
        expected = dict(class_=dict(good="class"), dict_=dict(good="dict"), list_=["list"])

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        [
            # fmt: off
            (pd.DataFrame({'a': [1, 2, 3], 'balloons': ['are', 'awesome', SimpleNamespace(floating='wicker', propelled_by='fire')]}),
             {'index': [0, 1, 2],
              'columns': ['a', 'balloons'],
              'data': [[1, 'are'], [2, 'awesome'], [3, dict(floating='wicker', propelled_by='fire')]]}),
            (pd.Series({0: 1, 1: 2, 2: SimpleNamespace(balloons="are awesome")}),
             {'index': [0, 1, 2],
              'data': [1, 2, dict(balloons="are awesome")]}),
            # fmt: on
        ],
    )
    def test_encode_pandas_recurse(value, expected) -> None:
        """
        Test recursive encoding of pandas objects
        """
        # Arrange

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected


class TestGetSnapshotFile:
    """ Tests for the get_snapshot_file utility function. """

    @staticmethod
    def test_get_snapshot_file(tmp_path):
        """ Test that get_snapshot_file returns the expected path. """
        # Arrange
        test_file = tmp_path / "example_test.py"
        suffix = ".json"
        expected = tmp_path / ".snapshots" / "example_test.json"

        # Act
        returned = get_snapshot_file(test_file, suffix)

        # Assert
        assert returned == expected
        assert returned.parent.exists()

    @staticmethod
    def test_get_snapshot_file_directory_error(tmp_path):
        """ Test that get_snapshot_file raises an error if the directory
        containing the test does not exist.
        """
        # Arrange
        test_file = tmp_path / "sub-directory" / "example_test.py"
        suffix = ".json"

        # Act & Assert
        with pytest.raises(NotADirectoryError):
            get_snapshot_file(test_file, suffix)

    @staticmethod
    def test_get_snapshot_file_type_error(tmp_path):
        """ Test that get_snapshot_file raises an error for an invalid suffix. """
        # Arrange
        test_file = tmp_path / "example_test.py"
        suffix = "json"

        # Act & Assert
        with pytest.raises(TypeError):
            get_snapshot_file(test_file, suffix)


class TestEncodingExceptions:
    """ Tests for exception encoding. """

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        # fmt: off
        [(ValueError("That's a bad value"),
          dict(exception_type="ValueError",
               exception_value="That's a bad value")),
         (OSError(2, "No such file or directory", "<><"),
          dict(exception_type="FileNotFoundError",
               exception_value="[Errno 2] No such file or directory: '<><'")),
         ]
        # fmt: on
    )
    def test_write_json_error(value, expected):
        """ Test if an error occurs during snapshot writing, no file is written. """
        # Arrange

        # Act
        result = encode_exception(value)

        # Assert
        assert result == expected
