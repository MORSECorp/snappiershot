""" Utilities for the serializers. """
import inspect
import warnings
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Set

from ..constants import ENCODING_FUNCTION_NAME, SNAPSHOT_DIRECTORY
from ..errors import SnappierShotWarning
from .constants import SERIALIZABLE_TYPES, JsonType
from .optional_module_utils import Numpy, Pandas


def filter_recursive_objects(
    func: Callable[[Any, Set[int]], JsonType]
) -> Callable[[Any, Optional[Set[int]]], JsonType]:
    """ Decorator object for catching and tracking recursive objects. """

    @wraps(func)
    def wrapper(value: Any, context: Optional[Set[int]] = None) -> JsonType:
        """ Wrapper function to catch and track recursive objects. """
        if context is None:
            context = set()

        object_id = id(value)
        if object_id in context:
            raise RecursionError(value)
        context.add(object_id)
        result = func(value, context)
        context.discard(object_id)
        return result

    return wrapper


@filter_recursive_objects
def default_encode_value(value: Any, context: Set[int]) -> JsonType:
    """ Perform a default encoding of the specified value into a serializable data. """
    # If the value is already serializable, return.
    if isinstance(value, SERIALIZABLE_TYPES):
        return value

    # If the value is a dict, recurse.
    if isinstance(value, Dict):
        encoded_dict = dict()
        for key, item in value.items():
            try:
                encoded_dict[key] = default_encode_value(item, context)
            except (ValueError, RecursionError) as err:
                if isinstance(err, RecursionError):
                    message = f"This object was determined to be recursive: {item} -- "
                else:
                    message = f"Cannot serialize this value: {item} -- "
                message += "Skipping over this (key, value) pair. "
                warnings.warn(message, SnappierShotWarning)

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
                encoded_sequence.append(default_encode_value(item, context))
            except (ValueError, RecursionError) as err:
                if isinstance(err, RecursionError):
                    message = f"This object was determined to be recursive: {item} -- "
                else:
                    message = f"Cannot serialize this value: {item} -- "
                message += "Skipping over this item. "
                warnings.warn(message, SnappierShotWarning)
        return encoded_sequence

    # If the value is a pandas object, encode and recurse
    if Pandas.is_pandas_object(value):
        return default_encode_value(Pandas.encode_pandas(value), context)

    # If the value is a numpy object, encode and recurse
    if Numpy.is_numpy_object(value):
        encoded_numpy = Numpy.encode_numpy(value)
        return default_encode_value(encoded_numpy)

    # If the value is an instanced class.
    if is_instanced_object(value):
        # If the class has specified an encoding function, call it.
        if hasattr(value, ENCODING_FUNCTION_NAME):
            return getattr(value, ENCODING_FUNCTION_NAME)()
        # Default to encoding the class dictionary.
        return default_encode_value(vars(value), context)

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
