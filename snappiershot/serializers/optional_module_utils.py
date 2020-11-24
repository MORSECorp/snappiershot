""" Utilities for handling optional modules """
from types import ModuleType
from typing import Any, Optional


def is_pandas_object(obj: Any) -> bool:
    """Return true if the given object is a pandas object

    A special effort is made to avoid importing pandas unless it's really necessary.
    As such, this is checked by looking for "pandas" in the __module__ attribute
    of the object's type

    """
    return "pandas" in getattr(type(obj), "__module__", "").split(".")


def get_pandas(
    raise_error: bool = False, custom_error_message: str = ""
) -> Optional[ModuleType]:
    """ Return pandas module, if it is already imported, otherwise return None

    Args:
        raise_error: if True, e.g. when pandas is required, raise an error
        custom_error_message: string, custom error message to use in place of default error message

    Returns:
        pandas module, or None if not found

    Raises:
        Import error if pandas is not found and import is required
    """
    try:
        import pandas as pd
    except ImportError as error:
        pd = None
        if raise_error:
            default_error_message = "pandas is required for snappiershot testing"
            raise ImportError(custom_error_message or default_error_message) from error
    return pd
