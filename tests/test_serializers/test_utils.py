""" Tests for snappiershot/serializers/utils.py """
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
