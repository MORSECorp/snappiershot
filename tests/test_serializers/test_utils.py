""" Tests for snappiershot/serializers/utils.py """
import pytest
from snappiershot.serializers.utils import get_snapshot_file


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


def test_get_snapshot_file_type_error(tmp_path):
    """ Test that get_snapshot_file raises an error for an invalid suffix. """
    # Arrange
    test_file = tmp_path / "example_test.py"
    suffix = "json"

    # Act & Assert
    with pytest.raises(TypeError):
        get_snapshot_file(test_file, suffix)
