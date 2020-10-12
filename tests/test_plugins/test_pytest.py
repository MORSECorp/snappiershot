""" Tests for snappiershot/plugins/pytest.py """
from pathlib import Path
from shutil import copytree

import pytest
from _pytest.pytester import Testdir
from snappiershot.plugins.pytest import PACKAGE_TRACKER_OPTION
from snappiershot.serializers.utils import SNAPSHOT_DIRECTORY
from snappiershot.snapshot import SnapshotStatus

PYTESTER_EXAMPLE_DIR = Path(__file__).parent / "pytester_example_dir"


@pytest.mark.filterwarnings("ignore:.*experimental api")
def test_tracker(testdir: Testdir):
    """ Test that the SnapshotTracker is able to track snapshot statuses
    throughout a pytest run.
    """
    # Arrange
    #   Load the test files into the testdir used by pytest to test plugins.
    copytree(PYTESTER_EXAMPLE_DIR / SNAPSHOT_DIRECTORY, testdir.tmpdir / SNAPSHOT_DIRECTORY)
    snapshot_file_1 = Path(testdir.tmpdir / ".snapshots" / "test_file_1.json")
    snapshot_file_2 = Path(testdir.tmpdir / ".snapshots" / "test_file_2.json")
    testdir.copy_example("test_file_1.py")
    testdir.copy_example("test_file_2.py")

    # Act
    #   Run pytest on the testdir (as quietly as possible).
    result = testdir.inline_run("-qq", "-s")

    # Assert
    #   Result is an object which tracks pytest hook calls. The last hook is
    #     "pytest_unconfigure" which allows us to access the pytest Config object
    #     used while running tests.
    config = result.calls[-1].config
    tracker = config.getoption(PACKAGE_TRACKER_OPTION)

    #   Assert that tracker collected the expected snapshot files.
    assert tracker.snapshot_files == {snapshot_file_1, snapshot_file_2}

    #   Assert that the tracker has the expected statuses for all snapshots.
    metadata = dict(
        arguments=dict(),
        test_runner_provided_name="",
        update_on_next_run=False,
        user_provided_name="",
    )
    assert tracker.snapshots == {
        snapshot_file_1: {
            "test_function_passed": [
                dict(metadata=metadata, snapshots=[SnapshotStatus.PASSED])
            ],
            "test_function_new": [
                dict(
                    metadata=metadata,
                    snapshots=[SnapshotStatus.PASSED, SnapshotStatus.WRITTEN],
                )
            ],
        },
        snapshot_file_2: {
            "test_function_fail": [
                dict(metadata=metadata, snapshots=[SnapshotStatus.FAILED])
            ],
            "test_function_unchecked": [
                dict(metadata=metadata, snapshots=[SnapshotStatus.UNCHECKED])
            ],
            "test_function_write": [
                dict(metadata=metadata, snapshots=[SnapshotStatus.WRITTEN])
            ],
        },
    }
