""" Serialization input/output utilities """
import json
from pathlib import Path
from typing import Dict, Optional

from ..constants import SnapshotKeys
from .json import JsonDeserializer, JsonSerializer, JsonType


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


def write_json_file(obj: JsonType, file: Path, indent: Optional[int] = None) -> None:
    """ Safely write a JSON file using the JsonSerializer.

    The file will first be written to a temporary file to avoid partial writing and
      errors during writing. Then the temporary file is moved to the specified location.
      The temporary file is always cleaned up.

    Args:
         obj: The obj to be serialized to JSON and written to file.
         file: The path to the output file.
         indent: The indentation for the JSON file. Defaults to json module's default.
    """
    temporary_file = file.with_suffix(".temp")
    try:
        with temporary_file.open("w") as snapshot_file:
            json.dump(obj, snapshot_file, cls=JsonSerializer, indent=indent, sort_keys=True)
        temporary_file.rename(file)
    finally:
        if temporary_file.exists():
            temporary_file.unlink()
