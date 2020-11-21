""" Utilities for the serializers. """
import inspect
import json
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from ..constants import (
    ENCODING_FUNCTION_NAME,
    SNAPSHOT_DIRECTORY,
    SnapshotKeys,
)
from ..errors import SnappierShotWarning
from .constants import SERIALIZABLE_TYPES, JsonType
from .json import JsonDeserializer, JsonSerializer


def default_encode_value(value: Any) -> JsonType:
    """ Perform a default encoding of the specified value into a serializable data. """
    # If the value is already serializable, return.
    if isinstance(value, SERIALIZABLE_TYPES):
        return value

    # If the value is a dict, recurse.
    if isinstance(value, Dict):
        encoded_dict = dict()
        for key, item in value.items():
            try:
                encoded_dict[key] = default_encode_value(item)
            except ValueError:
                warnings.warn(
                    f"Cannot serialize this value: {item} -- "
                    f"Skipping over this (key, value) pair. ",
                    SnappierShotWarning,
                )
        return encoded_dict

    # If the value is an exception. Every exception has unique hashes and therefore
    #   cannot automatically be compared.
    if isinstance(value, BaseException):
        return encode_exception(value)

    # If the value is a sequence, recurse.
    if isinstance(value, Sequence):
        encoded_sequence = list()
        for item in value:
            try:
                encoded_sequence.append(default_encode_value(item))
            except ValueError:
                warnings.warn(
                    f"Cannot serialize this value: {item} -- Skipping over this item. ",
                    SnappierShotWarning,
                )
        return encoded_sequence

    # If the value is an instanced class.
    if is_instanced_object(value):
        # If the class has specified an encoding function, call it.
        if hasattr(value, ENCODING_FUNCTION_NAME):
            return getattr(value, ENCODING_FUNCTION_NAME)()
        # Default to encoding the class dictionary.
        return default_encode_value(vars(value))

    raise ValueError(
        f"Cannot serialize this value: {value} \n"
        f"A default serialization for this type ({type(value)}) is not supported. "
        "You must either encode this value manually, or open an Issue on our Github "
        "page describing a default serialization for this type. "
    )


def encode_exception(value: BaseException) -> JsonType:
    """ Encode an exception object.

    These objects need to be specially handled because each exception has a unique
      hash and therefore cannot be automatically compared.

    The encoded format:
      {
        exception_type: <Exception Name>
        exception_message: <Exception Message>
      }

    Args:
        value: The exception object to be encoded.

    Returns:
        JSON serializable and comparable object.
    """
    return dict(exception_type=type(value).__name__, exception_value=str(value))


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


def is_instanced_object(value: Any) -> bool:
    """ Check if the input value is an instanced object, i.e. an instantiated class. """
    is_type = inspect.isclass(value)
    is_function = inspect.isroutine(value)
    is_object = hasattr(value, "__dict__")
    return is_object and not is_type and not is_function


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
