""" Tests for snappiershot/serializers/io.py """
import json

import pytest
from snappiershot.serializers.io import (
    SnapshotKeys,
    parse_snapshot_file,
    write_json_file,
)


class TestParseSnapshotFile:
    """Tests for the parse_snapshot_file utility function."""

    @staticmethod
    def test_parse_snapshot_file(tmp_path):
        """Test that parse_snapshot_file parses snapshot files as expected"""
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
        """Test that parse_snapshot_file raises an error when attempting to parse
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
        """Test that parse_snapshot_file raises an error when the contents of
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


class TestWritingToFile:
    """Tests for the file writing utility functions."""

    @staticmethod
    def test_write_json_error(tmp_path):
        """Test if an error occurs during snapshot writing, no file is written."""
        # Arrange
        obj = {("tuple as key",): None}
        snapshot_file = tmp_path / "snapshot_file.json"

        # Act
        try:
            write_json_file(obj, snapshot_file)
        except TypeError:
            pass

        # Assert
        assert not snapshot_file.exists()
        assert not list(snapshot_file.parent.glob("*"))
