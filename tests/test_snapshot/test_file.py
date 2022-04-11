""" Tests for snappiershot/snapshot/_file.py """
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List

import pytest
from snappiershot.config import Config
from snappiershot.inspection import CallerInfo
from snappiershot.snapshot._file import _NO_SNAPSHOT, _SnapshotFile
from snappiershot.snapshot.metadata import SnapshotMetadata
from snappiershot.snapshot.status import SnapshotStatus


@pytest.mark.usefixtures("empty_caller_info", "snapshot_file")
class TestSnapshotFile:
    """Tests for the snappiershot.snapshot._SnapshotFile object."""

    @staticmethod
    def test_get_snapshot_file_error(config: Config, metadata: SnapshotMetadata):
        """Test that _SnapshotFile._get_snapshot_file raises an error when given an
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
        """Test that if the snapshot file does not exist, the file contents are set to
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
        """Test that the _SnapshotFile._find_snapshots method finds snapshots as expected
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
        """Test that the _SnapshotFile.get_snapshot method functions as expected.

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
        """Test that the _SnapshotFile.mark_failed method functions as expected."""
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        expected = [SnapshotStatus.FAILED]

        # Act
        snapshot_file.mark_failed(index=0)

        # Assert
        assert snapshot_file._snapshot_statuses == expected

    def test_mark_passed(self, config: Config, metadata: SnapshotMetadata):
        """Test that the _SnapshotFile.mark_passed method functions as expected."""
        # Arrange
        snapshot_file = _SnapshotFile(config, metadata)
        expected = [SnapshotStatus.PASSED]

        # Act
        snapshot_file.mark_passed(index=0)

        # Assert
        assert snapshot_file._snapshot_statuses == expected

    @staticmethod
    def test_record_snapshot(config: Config, metadata: SnapshotMetadata):
        """Test that the _SnapshotFile.record_snapshot method functions as expected.

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
        """Test that the write method only writes when a changes are flagged."""
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

    @staticmethod
    def test_encoded_metadata(config: Config, snapshot_file: Path):
        """Test that SnapshotMetadata gets encoded to eliminate serialization errors."""
        # Arrange
        args = dict(unhandled_type=SimpleNamespace(complex=3 + 4j))
        caller_info = CallerInfo(snapshot_file, "test_function", args)
        metadata = SnapshotMetadata(caller_info, update_on_next_run=False)
        snapshot_file_object = _SnapshotFile(config, metadata)

        # Act
        snapshot_file_object._changed_flag = True
        snapshot_file_object.write()

        # Assert
        assert snapshot_file.exists()
        print(snapshot_file.read_text())
