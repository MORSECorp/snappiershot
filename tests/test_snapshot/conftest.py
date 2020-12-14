""" Shared fixtures for testing the snapshot module. """
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from snappiershot.config import Config
from snappiershot.inspection import CallerInfo
from snappiershot.snapshot._file import _SnapshotFile
from snappiershot.snapshot.metadata import SnapshotMetadata
from snappiershot.snapshot.snapshot import Snapshot


@pytest.fixture(name="config")
def _config() -> Config:
    """ Construct a default Config object to be used for all tests. """
    return Config()


@pytest.fixture(name="empty_caller_info")
def _empty_caller_info(tmp_path: Path, mocker: MockerFixture) -> CallerInfo:
    """ Mocks the call to the "from_call_stack" method of snappiershot.inspection.CallerInfo.

    The method returns an CallerInfo object that contains no arguments.
    """
    empty_caller_info = CallerInfo(tmp_path, "test_function", args=dict())
    mocker.patch(
        "snappiershot.snapshot.snapshot.CallerInfo.from_call_stack",
        return_value=empty_caller_info,
    )
    return empty_caller_info


@pytest.fixture(name="metadata")
def _metadata(empty_caller_info: CallerInfo) -> SnapshotMetadata:
    """ Construct a default SnapshotMetadata object. """
    return SnapshotMetadata(empty_caller_info, update_on_next_run=False)


@pytest.fixture(name="snapshot_file")
def _snapshot_file(tmp_path: Path, mocker: MockerFixture) -> Path:
    """ Mocks the call to the snappiershot.serializers.utils.get_snapshot_file. """
    snapshot_file = tmp_path.joinpath("snapshot.json")
    mocker.patch(
        "snappiershot.snapshot._file.get_snapshot_file", return_value=snapshot_file
    )
    return snapshot_file


@pytest.fixture(name="snapshot")
@pytest.mark.usefixtures("snapshot_file")
def _snapshot(config: Config, metadata: SnapshotMetadata) -> Snapshot:
    """ Returns a snappiershot.snapshot.Snapshot object with preset
    _metadata and _snapshot_file attributes.
    """
    snapshot = Snapshot()
    snapshot._metadata = metadata
    snapshot._snapshot_file = _SnapshotFile(config=config, metadata=metadata)
    snapshot._within_context = True
    return snapshot
