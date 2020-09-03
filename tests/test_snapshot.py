""" Tests for snappiershot/snapshot.py """
from pathlib import Path
from typing import Dict, Type

import pytest
from pytest_mock import MockerFixture
from snappiershot.config import Config
from snappiershot.inspection import CallerInfo
from snappiershot.snapshot import Snapshot, SnapshotMetadata

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
    MockSnapshotMetadata = mocker.patch("snappiershot.snapshot.SnapshotMetadata")
    MockSnapshotMetadata.return_value = SnapshotMetadata(
        caller_info=FAKE_CALLER_INFO, update_on_next_run=False
    )
    snapshot = Snapshot(configuration=Config())
    snapshot.value = {"balloons": "are awesome"}
    value = {"balloons": "are awesome"}

    # Act
    result = snapshot.assert_match(value=value, approximate=False)

    # Assert
    assert result


def test_snapshot_assert_failure(mocker: MockerFixture) -> None:
    """ Checks that snapshot assert works as expected with mis-matched values"""
    # Arrange
    MockSnapshotMetadata = mocker.patch("snappiershot.snapshot.SnapshotMetadata")
    MockSnapshotMetadata.return_value = SnapshotMetadata(
        caller_info=FAKE_CALLER_INFO, update_on_next_run=False
    )
    snapshot = Snapshot(configuration=Config())
    snapshot.value = {"balloons": "are awesome"}
    value = {"balloons": "are not awesome"}

    # Act / Assert
    with pytest.raises(AssertionError):
        snapshot.assert_match(value=value, approximate=False)


def test_snapshot_update(mocker: MockerFixture) -> None:
    """ Checks that snapshot assert with update flag ON works as expected """
    # Arrange
    MockSnapshotMetadata = mocker.patch("snappiershot.snapshot.SnapshotMetadata")
    MockSnapshotMetadata.return_value = SnapshotMetadata(
        caller_info=FAKE_CALLER_INFO, update_on_next_run=True
    )
    snapshot = Snapshot(configuration=Config())
    snapshot.value = {"balloons": "are awesome"}
    value = {"balloons": "are awesome"}
    mock_udpate_snapshot = mocker.patch.object(snapshot, "_update_snapshot")

    # Act
    result = snapshot.assert_match(value=value, approximate=False)

    # Assert
    assert result
    assert mock_udpate_snapshot.call_count == 1
