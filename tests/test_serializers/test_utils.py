""" Tests for snappiershot/serializers/utils.py """
import json

import pytest
from snappiershot.serializers.utils import (
    SnapshotKeys,
    get_snapshot_file,
    parse_snapshot_file,
)


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
