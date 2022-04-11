""" Tests for snappiershot/plugins/tracker.py """
from pathlib import Path

from snappiershot.inspection import CallerInfo
from snappiershot.plugins.tracker import SnapshotTracker, StatusReport
from snappiershot.snapshot import SnapshotMetadata, SnapshotStatus


def test_tracker_get_status_report():
    """Test that the SnapshotTracker.get_status_report method functions as expected."""
    # Arrange
    expected = StatusReport(1, 2, 3, 4, 5)

    tracker = SnapshotTracker()
    snapshot_file = Path(__file__)
    function_name = "test_function"
    metadata = SnapshotMetadata(
        caller_info=CallerInfo(snapshot_file, function_name, dict()),
        update_on_next_run=False,
        test_runner_provided_name="",
        user_provided_name="",
    )
    tracker.snapshots = {
        snapshot_file: {
            function_name: [
                dict(
                    metadata=metadata.as_dict(),
                    snapshots=[SnapshotStatus.UNCHECKED] * expected.unchecked,
                ),
                dict(
                    metadata=metadata.as_dict(),
                    snapshots=[SnapshotStatus.FAILED] * expected.failed,
                ),
                dict(
                    metadata=metadata.as_dict(),
                    snapshots=[SnapshotStatus.PASSED] * expected.passed,
                ),
                dict(
                    metadata=metadata.as_dict(),
                    snapshots=[SnapshotStatus.RECORDED] * expected.recorded,
                ),
                dict(
                    metadata=metadata.as_dict(),
                    snapshots=[SnapshotStatus.WRITTEN] * expected.written,
                ),
            ]
        }
    }

    # Act
    status_report = tracker.get_status_report()

    # Assert
    assert status_report == expected


def test_tracker_set_status():
    """Test that the SnapshotTracker.set_status method functions as expected."""
    # Arrange
    statuses = [
        SnapshotStatus.UNCHECKED,
        SnapshotStatus.PASSED,
        SnapshotStatus.WRITTEN,
        SnapshotStatus.FAILED,
    ]
    snapshot_file = Path(__file__)
    function_name = "test_function"
    metadata = SnapshotMetadata(
        caller_info=CallerInfo(snapshot_file, function_name, dict()),
        update_on_next_run=False,
        test_runner_provided_name="",
        user_provided_name="",
    )

    # Act
    tracker = SnapshotTracker()
    tracker.set_status(
        statuses=statuses,
        snapshot_file=snapshot_file,
        function_name=function_name,
        metadata=metadata,
    )

    # Assert
    assert tracker.snapshots == {
        snapshot_file: {
            function_name: [dict(metadata=metadata.as_dict(), snapshots=statuses)]
        }
    }
