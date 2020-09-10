""" Tests for snappiershot/snapshot.py """
from pathlib import Path
from typing import Dict, Type

import pytest
from pytest_mock import MockerFixture
from snappiershot import CallerInfo, Snapshot, SnapshotMetadata

FAKE_CALLER_INFO = CallerInfo(
    file=Path("fake/file/path"),
    function="fake_fully_qualified_function_name",
    args={"foo": 1, "bar": "two"},
)

DEFAULT_METADATA_KWARGS = dict(
    caller_info=FAKE_CALLER_INFO,
    update_on_next_run=False,
    test_runner_provided_name="",
    user_provided_name="",
)


@pytest.mark.parametrize(
    "metadata_kwargs, expected_error",
    [
        ({**DEFAULT_METADATA_KWARGS, "caller_info": None}, TypeError),
        ({**DEFAULT_METADATA_KWARGS, "update_on_next_run": "foo"}, TypeError),
        ({**DEFAULT_METADATA_KWARGS, "test_runner_provided_name": 1.23}, TypeError),
        ({**DEFAULT_METADATA_KWARGS, "user_provided_name": 1.23}, TypeError),
    ],
)
def test_metadata_validate(metadata_kwargs: Dict, expected_error: Type[Exception]):
    """ Checks that validation of the metadata values occurs as expected. """
    # Arrange

    # Act & Assert
    with pytest.raises(expected_error):
        SnapshotMetadata(**metadata_kwargs)


def test_snapshot_assert(mocker: MockerFixture) -> None:
    """ Checks that snapshot assert works as expected """
    # Arrange
    # Snapshot object under test
    snapshot = Snapshot()

    # Mock snapshot metadata for testing
    test_metadata = SnapshotMetadata(caller_info=FAKE_CALLER_INFO, update_on_next_run=False)
    mocker.patch.object(snapshot, "_get_metadata", return_value=test_metadata)

    # Mock stored snapshot value
    value = {"balloons": "are awesome"}
    mocker.patch.object(snapshot, "_get_value", return_value=value)

    # Act
    result = snapshot.assert_match(value=value)

    # Assert
    assert result


def test_snapshot_assert_failure(mocker: MockerFixture) -> None:
    """ Checks that snapshot assert works as expected with mis-matched values"""
    # Arrange
    # Snapshot object under test
    snapshot = Snapshot()

    # Mock snapshot metadata for testing
    test_metadata = SnapshotMetadata(caller_info=FAKE_CALLER_INFO, update_on_next_run=False)
    mocker.patch.object(snapshot, "_get_metadata", return_value=test_metadata)

    # Mock stored snapshot value
    value = {"balloons": "are awesome"}
    mocker.patch.object(snapshot, "_get_value", return_value=value)

    bad_value = {"balloons": "are not awesome"}

    # Act / Assert
    with pytest.raises(AssertionError):
        snapshot.assert_match(value=bad_value)


def test_snapshot_update(mocker: MockerFixture) -> None:
    """ Checks that snapshot assert with update flag ON works as expected """
    # Arrange
    # Snapshot object under test
    snapshot = Snapshot()

    # Mock snapshot metadata for testing
    test_metadata = SnapshotMetadata(caller_info=FAKE_CALLER_INFO, update_on_next_run=True)
    mocker.patch.object(snapshot, "_get_metadata", return_value=test_metadata)

    # Mock stored snapshot value
    value = {"balloons": "are awesome"}
    mocker.patch.object(snapshot, "_get_value", return_value=value)

    # Mock update snapshot functionality
    mock_udpate_snapshot = mocker.patch.object(snapshot, "_update_snapshot")

    # Act
    result = snapshot.assert_match(value=value)

    # Assert
    assert result
    assert mock_udpate_snapshot.call_count == 1
