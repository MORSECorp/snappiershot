""" Utilities for the serializers. """
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict

from .json import JsonDeserializer

SNAPSHOT_DIRECTORY = ".snapshots"


class SnapshotKeys(SimpleNamespace):
    """ Centralized location for the names of the keys of the parsed snapshot file. """

    metadata = "metadata"
    tests = "tests"
    snapshots = "snapshots"
    update = "update_on_next_run"
    version = "snappiershot_version"


def get_snapshot_file(test_file: Path, suffix: str) -> Path:
    """ Returns the path to the snapshot file.

    The SNAPSHOT_DIRECTORY will be created automatically if it does not exist.

    Args:
        test_file: The path to the test file.
        suffix: The file extension for the snapshot file.
          Should include the dot, e.g. ".json"
    """
    # Error checking.
    if not test_file.parent.exists():
        raise NotADirectoryError(
            f"The directory containing the test file does not exist: {test_file.parent}"
        )
    if not suffix.startswith("."):
        raise TypeError(
            'Suffix is not a valid file extension; it must start with a "dot", i.e. ".json"'
            f" -- Found: {suffix}"
        )

    snapshot_directory = test_file.parent.joinpath(SNAPSHOT_DIRECTORY)
    snapshot_directory.mkdir(exist_ok=True)
    return snapshot_directory.joinpath(test_file.name).with_suffix(suffix)


def parse_snapshot_file(snapshot_file: Path) -> Dict:
    """ Parses the snapshot file.

    Args:
        snapshot_file: The path to the file containing snapshots.

    Raises:
        ValueError: If the file format of the snapshot_file is not supported or recognized.
    """
    if snapshot_file.suffix == ".json":
        with snapshot_file.open() as json_file:
            file_contents = json.load(json_file, cls=JsonDeserializer)
    else:
        raise ValueError(f"Unsupported snapshot file format: {snapshot_file.suffix}")

    contains_version = SnapshotKeys.version in file_contents
    contains_tests = SnapshotKeys.tests in file_contents
    if not (contains_tests and contains_version):
        raise ValueError(
            f"Invalid snapshot file detected: {snapshot_file} \n"
            f"Expected top-level keys: {SnapshotKeys.version}, {SnapshotKeys.tests}"
        )
    return file_contents
