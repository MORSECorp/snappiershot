""" Tests for snappiershot/snapshot.py """
import json
from pathlib import Path
from typing import Dict, List, Type

import pytest
from pytest_mock import MockerFixture
from snappiershot.snapshot import (
    _NO_SNAPSHOT,
    CallerInfo,
    Config,
    Snapshot,
    SnapshotMetadata,
    SnapshotStatus,
    _SnapshotFile,
)


# ===== Fixtures ===========================================
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
        "snappiershot.snapshot.CallerInfo.from_call_stack", return_value=empty_caller_info
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
    mocker.patch("snappiershot.snapshot.get_snapshot_file", return_value=snapshot_file)
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


# ===== Unit Tests =========================================


class TestSnapshotMetadata:
    """ Tests for the snappiershot.snapshot.SnapshotMetadata object. """

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

    @staticmethod
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

    @staticmethod
    @pytest.mark.parametrize(
        "metadata_kwargs, metadata_dict, matches",
        [
            (DEFAULT_METADATA_KWARGS, {"arguments": FAKE_CALLER_INFO.args}, True),
            (DEFAULT_METADATA_KWARGS, {"arguments": {"foo": 1, "bar": 2}}, False),
        ],
    )
    def test_metadata_matches(metadata_kwargs: Dict, metadata_dict: Dict, matches: bool):
        """ Checks that the SnapshotMetadata.matches method functions as expected. """
        # Arrange
        metadata = SnapshotMetadata(**metadata_kwargs)

        # Act
        result = metadata.matches(metadata_dict)

        # Assert
        assert result == matches


class TestSnapshot:
    """ Tests for the snappiershot.snapshot.Snapshot object. """

    @staticmethod
    def test_snapshot_assert(snapshot: Snapshot, mocker: MockerFixture) -> None:
        """ Checks that snapshot assert works as expected """
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
        """ Checks that snapshot assert works as expected with mis-matched values"""
        # Arrange
        # Mock stored snapshot value
        value = {"balloons": "are awesome"}
        mocker.patch.object(snapshot._snapshot_file, "get_snapshot", return_value=value)

        bad_value = {"balloons": "are not awesome"}

        # Act / Assert
        with pytest.raises(AssertionError):
            snapshot.assert_match(value=bad_value)

    @staticmethod
    def test_snapshot_update(snapshot: Snapshot, mocker: MockerFixture) -> None:
        """ Checks that snapshot assert with update flag ON works as expected.

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


@pytest.mark.usefixtures("empty_caller_info", "snapshot_file")
class TestSnapshotFile:
    """ Tests for the snappiershot.snapshot._SnapshotFile object. """

    @staticmethod
    def test_get_snapshot_file_error(config: Config, metadata: SnapshotMetadata):
        """ Test that _SnapshotFile._get_snapshot_file raises an error when given an
        unsupported file format.
        """
        # Arrange
        config.file_format = "JPEG"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            _SnapshotFile(config, metadata)

        # Assert that the correct method raised the exception.
        assert exc_info.match(f"{config.file_format}$")

    @staticmethod
    def test_parse_snapshot_file_no_file(config: Config, metadata: SnapshotMetadata):
        """ Test that if the snapshot file does not exist, the file contents are set to
        an empty, default value.
        """
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        expected = snapshot_file._empty_file_contents

        # Act
        result = snapshot_file._parse_snapshot_file(snapshot_file._snapshot_file)

        # Assert
        assert result == expected

    _metadata_dict = dict(
        user_provided_name="",
        test_runner_provided_name="",
        update_on_next_run=False,
        arguments=dict(),
    )

    @staticmethod
    @pytest.mark.parametrize(
        "contents, expected_contents, expected_snapshots",
        [
            (
                {"snappiershot_version": "X.X.X", "tests": {}},
                {
                    "snappiershot_version": "X.X.X",
                    "tests": {
                        "test_function": [{"metadata": _metadata_dict, "snapshots": []}]
                    },
                },
                [],
            ),
            (
                {
                    "snappiershot_version": "X.X.X",
                    "tests": {
                        "other_function": [
                            {"metadata": _metadata_dict, "snapshots": ["snapshot_1"]}
                        ]
                    },
                },
                {
                    "snappiershot_version": "X.X.X",
                    "tests": {
                        "other_function": [
                            {"metadata": _metadata_dict, "snapshots": ["snapshot_1"]}
                        ],
                        "test_function": [{"metadata": _metadata_dict, "snapshots": []}],
                    },
                },
                [],
            ),
            (
                {
                    "snappiershot_version": "X.X.X",
                    "tests": {
                        "test_function": [
                            {"metadata": _metadata_dict, "snapshots": ["snapshot_1"]}
                        ]
                    },
                },
                {
                    "snappiershot_version": "X.X.X",
                    "tests": {
                        "test_function": [
                            {"metadata": _metadata_dict, "snapshots": ["snapshot_1"]}
                        ]
                    },
                },
                ["snapshot_1"],
            ),
        ],
    )
    def test_find_snapshots(
        contents: Dict,
        expected_contents: Dict,
        expected_snapshots: List,
        config: Config,
        metadata: SnapshotMetadata,
        snapshot_file: Path,
    ):
        """ Test that the _SnapshotFile._find_snapshots method finds snapshots as expected
        and updates the _file_contents attribute as expected.
        """
        # Arrange
        snapshot_file.write_text(json.dumps(contents))

        # Act
        snapshot_file_object = _SnapshotFile(config, metadata)

        # Assert
        assert snapshot_file_object._file_contents == expected_contents
        assert snapshot_file_object._snapshots == expected_snapshots

    @staticmethod
    @pytest.mark.parametrize(
        "snapshots, index, expected",
        [(["A", "B", "C"], 1, "B"), (["A", "B", "C"], 4, _NO_SNAPSHOT)],
    )
    def test_get_snapshot(
        snapshots, index, expected, config: Config, metadata: SnapshotMetadata
    ):
        """ Test that the _SnapshotFile.get_snapshot method functions as expected.

        Additionally assert that no changes are flagged from reading snapshots.
        """
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        snapshot_file._snapshots = snapshots

        # Act
        result = snapshot_file.get_snapshot(index)

        # Assert
        assert result == expected
        assert not snapshot_file._changed_flag

    def test_mark_failed(self, config: Config, metadata: SnapshotMetadata):
        """ Test that the _SnapshotFile.mark_failed method functions as expected. """
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        expected = [SnapshotStatus.FAILED]

        # Act
        snapshot_file.mark_failed(index=0)

        # Assert
        assert snapshot_file._snapshot_statuses == expected

    def test_mark_passed(self, config: Config, metadata: SnapshotMetadata):
        """ Test that the _SnapshotFile.mark_passed method functions as expected. """
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        expected = [SnapshotStatus.PASSED]

        # Act
        snapshot_file.mark_passed(index=0)

        # Assert
        assert snapshot_file._snapshot_statuses == expected

    @staticmethod
    def test_record_snapshot(config: Config, metadata: SnapshotMetadata):
        """ Test that the _SnapshotFile.record_snapshot method functions as expected.

        Additionally assert that changes are flagged when recording snapshots.
        """
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        expected_statuses = [SnapshotStatus.RECORDED, SnapshotStatus.RECORDED]

        # Act
        snapshot_file.record_snapshot("A")
        snapshot_file.record_snapshot("B")
        snapshot_file.record_snapshot("C", index=0)

        # Assert
        assert snapshot_file._snapshots == ["C", "B"]
        assert snapshot_file._changed_flag
        assert snapshot_file._snapshot_statuses == expected_statuses

    @staticmethod
    @pytest.mark.parametrize("changed_flag, file_written", [(False, False), (True, True)])
    def test_write(
        changed_flag,
        file_written,
        config: Config,
        metadata: SnapshotMetadata,
        snapshot_file: Path,
    ):
        """ Test that the write method only writes when a changes are flagged. """
        # Arrange
        snapshot_file_object = _SnapshotFile(config, metadata)
        snapshot_file_object._changed_flag = changed_flag
        snapshot_file_object._snapshot_statuses = [
            SnapshotStatus.PASSED,
            SnapshotStatus.RECORDED,
        ]
        expected_statuses = [SnapshotStatus.PASSED, SnapshotStatus.WRITTEN]

        # Act
        snapshot_file_object.write()

        # Assert
        assert snapshot_file.exists() == file_written
        if file_written:
            assert snapshot_file_object._snapshot_statuses == expected_statuses
