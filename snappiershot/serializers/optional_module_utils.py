""" Utilities for handling optional modules """
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple

EncodedPandasType = Dict[str, List[Any]]


class Pandas:
    @staticmethod
    def is_pandas_object(obj: Any) -> bool:
        """Return true if the given object is a pandas object

        A special effort is made to avoid importing pandas unless it's really necessary.
        As such, this is checked by looking for "pandas" in the __module__ attribute
        of the object's type

        """
        return "pandas" in getattr(type(obj), "__module__", "").split(".")

    @staticmethod
    def get_pandas(
        raise_error: bool = False, custom_error_message: str = ""
    ) -> Optional[ModuleType]:
        """Return pandas module, if it is already imported, otherwise return None

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
                default_error_message = "pandas is required for snappiershot testing when snapshotting pandas objects"
                raise ImportError(custom_error_message or default_error_message) from error
        return pd

    @classmethod
    def encode_pandas(cls, value: Any) -> EncodedPandasType:
        """Encoding given pandas object as a dictionary

        Raises:
            NotImplementedError - If encoding is not implemented for the given pandas type.
        """
        # A special effort is made to avoid importing pandas unless it's really necessary.
        pd = cls.get_pandas(raise_error=True)

        if isinstance(value, pd.DataFrame):  # type: ignore
            encoded_value = value.to_dict("split")
            return encoded_value

        if isinstance(value, pd.Series):  # type: ignore
            encoded_value = {
                "data": value.to_list(),
                "index": value.index.to_list(),
            }
            return encoded_value

        raise NotImplementedError(
            f"No encoding implemented for the following pandas type: {value} ({type(value)})"
        )


class Numpy:

    _primative_names = (
        "bool_",
        "byte",
        "ubyte",
        "short",
        "ushort",
        "intc",
        "uintc",
        "int_",
        "uint",
        "longlong",
        "ulonglong",
        "float16",
        "single",
        "double",
        "longdouble",
        "csingle",
        "cdouble",
        "clongdouble",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "intp",
        "uintp",
        "float32",
        "float64",
        "complex64",
        "complex128",
        "complex_",
    )

    @staticmethod
    def is_numpy_object(obj: Any) -> bool:
        """Return true if the given object is a numpy array

        A special effort is made to avoid importing numpy unless it's really necessary.
        As such, this is checked by looking for "numpy" in the __module__ attribute
        of the object's type

        """
        return "numpy" in getattr(type(obj), "__module__", "").split(".")

    @staticmethod
    def get_numpy(
        raise_error: bool = False, custom_error_message: str = ""
    ) -> Optional[ModuleType]:
        """Return numpy module, if it is already imported, otherwise return None

        Args:
            raise_error: if True, e.g. when numpy is required, raise an error
            custom_error_message: string, custom error message to use in place of default error message

        Returns:
            numpy module, or None if not found

        Raises:
            Import error if numpy is not found and import is required
        """
        try:
            import numpy as np
        except ImportError as error:
            np = None
            if raise_error:
                default_error_message = "numpy is required for snappiershot testing when snapshotting numpy arrays"
                raise ImportError(custom_error_message or default_error_message) from error
        return np

    @classmethod
    def _get_numpy_primatives(cls, np: ModuleType) -> Tuple[type]:
        """Get numpy primative types
        Based on https://numpy.org/devdocs/user/basics.types.html

        Args:
            np: numpy module

        Returns:
            Tuple of numpy primative types
        """
        primative_types = tuple(
            [
                getattr(np, name, None)
                for name in cls._primative_names
                if getattr(np, name, None) is not None
            ]
        )
        return primative_types  # type: ignore

    @classmethod
    def encode_numpy(cls, value: Any) -> Any:
        """Encoding given numpy object

        Raises:
            NotImplementedError - If encoding is not implemented for the given numpy type.
        """
        # A special effort is made to avoid importing numpy unless it's really necessary.
        np = cls.get_numpy(raise_error=True)

        if isinstance(value, np.ndarray):  # type: ignore
            return value.tolist()

        if isinstance(value, cls._get_numpy_primatives(np)):
            return value.item()  # type: ignore

        raise NotImplementedError(
            f"No encoding implemented for the following numpy type: {value} ({type(value)})"
        )
