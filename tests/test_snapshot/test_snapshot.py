""" Tests for snappiershot/snapshot/snapshot.py """
from typing import List
from warnings import WarningMessage

import pytest
from pytest_mock import MockerFixture
from snappiershot.errors import SnappierShotWarning
from snappiershot.serializers.utils import encode_exception
from snappiershot.snapshot.snapshot import Snapshot


class TestSnapshot:
    """Tests for the snappiershot.snapshot.Snapshot object."""

    @staticmethod
    def test_snapshot_assert(snapshot: Snapshot, mocker: MockerFixture) -> None:
        """Checks that snapshot assert works as expected"""
        # Arrange
        # Mock stored snapshot value
        value = {"balloons": "are awesome"}
        mocker.patch.object(snapshot._snapshot_file, "get_snapshot", return_value=value)

        # Act
        result = snapshot.assert_match(value=value)

        # Assert
        assert result

    @staticmethod
    def test_snapshot_assert_failure(snapshot: Snapshot, mocker: MockerFixture) -> None:
        """Checks that snapshot assert works as expected with mis-matched values"""
        # Arrange
        # Mock stored snapshot value
        value = {"balloons": "are awesome"}
        mocker.patch.object(snapshot._snapshot_file, "get_snapshot", return_value=value)

        bad_value = {"balloons": "are not awesome"}

        # Act / Assert
        with pytest.raises(AssertionError):
            snapshot.assert_match(value=bad_value)

    @staticmethod
    def test_snapshot_update(
        snapshot: Snapshot, mocker: MockerFixture, warning_catcher: List[WarningMessage]
    ) -> None:
        """Checks that snapshot assert with update flag ON works as expected.

        If "update" is flagged, then no AssertionError should be raised.
        """
        # Arrange
        # Mock stored snapshot value
        value = {"balloons": "are awesome"}
        mocker.patch.object(snapshot._snapshot_file, "get_snapshot", return_value=value)

        new_value = {"balloons": "are not awesome"}

        # Act
        result = snapshot.assert_match(value=new_value, update=True)

        # Assert
        assert result
        assert warning_catcher
        assert warning_catcher[0].category == SnappierShotWarning

    @staticmethod
    def test_construct_diff(mocker: MockerFixture):
        """Test that the human-readable diff is constructed as expected."""
        # Arrange
        value = False
        expected = 3 + 4j
        comparison = mocker.MagicMock()

        summary_message = "Types not equal: <class 'bool'> != <class 'complex'>"
        comparison.differences.items = dict(msg=summary_message)
        expected_diff = f"""
- False
+ (3+4j)
------------------------------------------------------------------------------
Summary:
  > {summary_message}
""".lstrip(
            "\n"
        )  # Strip the newline from the start.

        # Act
        result = Snapshot._construct_diff(value, expected, comparison)

        # Assert
        assert result == expected_diff

    @staticmethod
    def test_not_within_context(mocker: MockerFixture):
        """Test that an error is raised when trying to call the `Snapshot.assert_match`
        method outside of context."""
        # Arrange
        snapshot = Snapshot()
        # Safety mock, should not get called.
        mocker.patch.object(snapshot, "_get_metadata", side_effect=EnvironmentError)

        # Act & Assert
        with pytest.raises(RuntimeError):
            snapshot.assert_match(True)

    @staticmethod
    def test_raises_match(snapshot: Snapshot, mocker: MockerFixture):
        """Test that `Snapshot.raises` catches and snapshot exceptions as expected."""
        # Arrange
        exception = ZeroDivisionError("Whoops")
        value = encode_exception(exception)
        mocker.patch.object(snapshot._snapshot_file, "get_snapshot", return_value=value)

        # Act
        with snapshot.raises(type(exception)) as raises:
            raise exception

        # Assert
        assert raises._assert_match

    @staticmethod
    @pytest.mark.parametrize(
        "expected_exception, update",
        [
            (None, False),
            (int, False),
            ({OSError, KeyError}, False),
            ((OSError, None), False),
        ],
    )
    def test_raises_type_errors(expected_exception, update, snapshot: Snapshot):
        """Test that `Snapshot.raises` rejects invalid argument types."""
        # Arrange

        # Act & Assert
        with pytest.raises(TypeError):
            snapshot.raises(expected_exception, update=update)
