""" Tests for snappiershot/inspection.py """
from pathlib import Path
from typing import Callable, Tuple

import pytest
from snappiershot.inspection import CallerInfo, is_staticmethod

FILE = Path(__file__)
Result_Expected = Tuple[CallerInfo, CallerInfo]


# ===== Test Objects =======================================


def get_caller_info(frame_index: int = 2) -> CallerInfo:
    """Calls the `snappiershot.inspection.CallerInfo.from_call_stack` method.

    This simulates the expected call stack during normal snappiershot runtime.

    Returns:
        The resultant CallerInfo object.
    """
    return CallerInfo.from_call_stack(frame_index)


def single_function_no_args() -> Result_Expected:
    """Single function call, with no arguments."""
    expected = CallerInfo(FILE, "single_function_no_args", {})
    return get_caller_info(), expected


def single_function_with_args(
    foo: str = "FOO", bar: bool = True, pi: float = 3.14
) -> Result_Expected:
    """Single function call, with arguments."""
    expected = CallerInfo(FILE, "single_function_with_args", dict(foo=foo, bar=bar, pi=pi))
    return get_caller_info(), expected


def nested_function() -> Result_Expected:
    """Nested function call."""

    def inner():
        """Inner (nested) function."""
        return get_caller_info(frame_index=3)

    expected = CallerInfo(FILE, "nested_function", {})
    return inner(), expected


class ClassTestObject:
    """Class used for housing more test objects."""

    # noinspection PyMethodMayBeStatic
    def method(self) -> Result_Expected:
        """Method call."""
        expected = CallerInfo(FILE, "ClassTestObject.method", {})
        return get_caller_info(), expected

    @classmethod
    def classmethod_(cls) -> Result_Expected:
        """Class method call."""
        expected = CallerInfo(FILE, "ClassTestObject.classmethod_", {})
        return get_caller_info(), expected

    @staticmethod
    def staticmethod_() -> Result_Expected:
        """Static method call."""
        expected = CallerInfo(FILE, "ClassTestObject.staticmethod_", {})
        return get_caller_info(), expected

    # noinspection PyMethodMayBeStatic, PyMethodParameters
    def method_no_self_arg(notself) -> Result_Expected:
        """Method call, but the "self" argument is mis-named."""
        expected = CallerInfo(FILE, "ClassTestObject.method_no_self_arg", {})
        return get_caller_info(), expected

    # noinspection PyMethodParameters
    @classmethod
    def classmethod_no_self_arg(notcls) -> Result_Expected:
        """Class method call, but the "self" argument is mis-named."""
        expected = CallerInfo(FILE, "ClassTestObject.classmethod_no_self_arg", {})
        return get_caller_info(), expected

    # noinspection PyUnusedLocal
    @staticmethod
    def staticmethod_self_arg(self=None) -> Result_Expected:
        """Static method call, but the first argument is "self"."""
        expected = CallerInfo(
            FILE, "ClassTestObject.staticmethod_self_arg", dict(self=None)
        )
        return get_caller_info(), expected

    # noinspection PyUnusedLocal
    @staticmethod
    def staticmethod_cls_arg(cls=None) -> Result_Expected:
        """Static method call, but the first argument is "cls"."""
        expected = CallerInfo(FILE, "ClassTestObject.staticmethod_cls_arg", dict(cls=None))
        return get_caller_info(), expected

    class NestedClass:
        """Nest class definition."""

        # noinspection PyMethodMayBeStatic
        def method(self) -> Result_Expected:
            """Method call within nested class definition."""
            expected = CallerInfo(FILE, "ClassTestObject.NestedClass.method", {})
            return get_caller_info(), expected

        @staticmethod
        def staticmethod() -> Result_Expected:
            """Static method call."""
            expected = CallerInfo(FILE, "ClassTestObject.NestedClass.staticmethod", {})
            return get_caller_info(), expected


# ===== Tests ==============================================


@pytest.mark.parametrize(
    "function",
    [
        single_function_no_args,
        single_function_with_args,
        nested_function,
        ClassTestObject().method,
        ClassTestObject.classmethod_,
        ClassTestObject.staticmethod_,
        ClassTestObject().method_no_self_arg,
        ClassTestObject.classmethod_no_self_arg,
        ClassTestObject.staticmethod_self_arg,
        ClassTestObject.staticmethod_cls_arg,
        ClassTestObject.NestedClass().method,
        ClassTestObject.NestedClass.staticmethod,
    ],
)
def test_caller_function_inspection(function: Callable[..., Result_Expected]):
    """Tests that the CallerInfo.from_call_stack method can correctly extract
    information about the caller function.

    Args:
        function: A pre-baked function that calls the CallerInfo.from_call_stack
          method and returns a tuple of the result of that call and the expected
          CallerInfo object. These can then be asserted against each other.
    """
    # Arrange

    # Act
    result, expected = function()

    # Assert
    assert result == expected


def test_caller_function_inspection_inner_function_error():
    """Tests that the CallerInfo.from_call_stack method raises an error if
    it cannot determine the caller function due to that function being defined
    within another functions scope.
    """
    # Arrange

    def inner():
        """Inner function definition."""
        CallerInfo.from_call_stack(1)

    # Act & Assert
    with pytest.raises(RuntimeError):
        inner()


@pytest.mark.parametrize(
    "cls, method, expected",
    [
        (ClassTestObject, "method", False),
        (ClassTestObject, "classmethod_", False),
        (ClassTestObject, "staticmethod_", True),
        (ClassTestObject, "staticmethod_self_arg", True),
        (ClassTestObject, "staticmethod_cls_arg", True),
        (ClassTestObject.NestedClass, "method", False),
        (ClassTestObject.NestedClass, "staticmethod", True),
        (ClassTestObject, "does-not-exist", False),
    ],
)
def test_is_staticmethod(cls: object, method: str, expected: bool):
    """Tests that the is_staticmethod function correctly identifies staticmethod."""
    # Arrange

    # Act
    result = is_staticmethod(cls, method)

    # Assert
    assert result == expected
