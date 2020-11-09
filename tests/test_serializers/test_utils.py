""" Tests for snappiershot/serializers/utils.py """
import json
from types import SimpleNamespace

import pytest
from snappiershot.serializers.utils import (
    SnapshotKeys,
    default_encode_value,
    get_snapshot_file,
    parse_snapshot_file,
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
        """ Test that a class with custom-encoded types dose not encode these types. """
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
        """ Test that a class with custom-encoded types dose not encode collection. """
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


class TestParseSnapshotFile:
    """ Tests for the parse_snapshot_file utility function. """

    @staticmethod
    def test_parse_snapshot_file(tmp_path):
        """ Test that parse_snapshot_file parses snapshot files as expected """
        # Arrange
        snapshot_file = tmp_path / "example_test.json"
        expected = {SnapshotKeys.version: "X.X.X", SnapshotKeys.tests: dict()}
        snapshot_file.write_text(json.dumps(expected))

        # Act
        returned = parse_snapshot_file(snapshot_file)

        # Assert
        assert returned == expected

    @staticmethod
    def test_parse_snapshot_file_format_error(tmp_path):
        """ Test that parse_snapshot_file raises an error when attempting to parse
        an unsupported file format for snapshot files.
        """
        # Arrange
        snapshot_file = tmp_path / "example_test.png"

        # Act & Assert
        with pytest.raises(ValueError):
            parse_snapshot_file(snapshot_file)

    @staticmethod
    @pytest.mark.parametrize(
        "contents", ["{}", '{"snappiershot_version": "X.X.X"}', '{"tests": {}}']
    )
    def test_parse_snapshot_file_error(contents: str, tmp_path):
        """ Test that parse_snapshot_file raises an error when the contents of
        the parsed snapshot file do not adhere to the snapshot file format.

        The snapshot format should be:
          {"snappiershot_version": "X.X.X", "tests": {...}}
        """
        # Arrange
        snapshot_file = tmp_path / "example_test.json"
        snapshot_file.write_text(contents)

        # Act & Assert
        with pytest.raises(ValueError):
            parse_snapshot_file(snapshot_file)
