""" Functionality for encoding a python object into a SnappierShotValue. """
from typing import Any, Dict, Iterable, List, Union

Primitive = Union[bool, int, float, None, str]
SnappiershotValue = Union[Primitive, Dict, List]


def encode_value(value: Any) -> SnappiershotValue:
    """ Encode a python object into a SnappierShot value.

    Raises:
        NotImplementedError - Encoding does not exist.
    """
    if isinstance(value, Primitive.__args__):  # type: ignore
        return value
    if _is_numpy_array(value):
        # The ``numpy.ndarray.tolist`` method is used here as opposed to the builtin
        #   ``list`` type conversion because it is more robust and works recursively.
        return encode_value(value.tolist())
    if isinstance(value, Iterable):
        return [encode_value(value) for value in value]
    raise NotImplementedError(f"The value specified has no encoding: {value}")


def _is_numpy_array(value: Any) -> bool:
    """ Determines if the input value is a numpy array in a import-safe manner.

    This implementation is pulled from ``_pytest.python_api._is_numpy_array``:
      https://github.com/pytest-dev/pytest/blob/f28af14/src/_pytest/python_api.py#L508
    """
    import sys

    np: Any = sys.modules.get("numpy")
    if np is not None:
        return isinstance(value, np.ndarray)
    return False  # pragma: no cover
