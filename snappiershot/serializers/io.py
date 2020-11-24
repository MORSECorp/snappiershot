""" Serialization input/output utilities """
import json
from pathlib import Path
from typing import Dict

from ..constants import SnapshotKeys
from .json import JsonDeserializer


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
