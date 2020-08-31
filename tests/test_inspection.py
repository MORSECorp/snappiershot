""" Tests for snappiershot/inspection.py """
from pathlib import Path
from typing import Callable, Tuple

import pytest
from snappiershot.inspection import CallerInfo

FILE = Path(__file__)
Result_Expected = Tuple[CallerInfo, CallerInfo]


# ===== Test Objects =======================================


def get_caller_info(frame_index: int = 2) -> CallerInfo:
    """ Calls the `snappiershot.inspection.CallerInfo.from_call_stack` method.

    This simulates the expected call stack during normal snappiershot runtime.

    Returns:
        The resultant CallerInfo object.
    """
    return CallerInfo.from_call_stack(frame_index)


def single_function_no_args() -> Result_Expected:
    """ Single function call, with no arguments. """
    expected = CallerInfo(FILE, "single_function_no_args", {})
    return get_caller_info(), expected


def single_function_with_args(
    foo: str = "FOO", bar: bool = True, pi: float = 3.14
) -> Result_Expected:
    """ Single function call, with arguments. """
    expected = CallerInfo(FILE, "single_function_with_args", dict(foo=foo, bar=bar, pi=pi))
    return get_caller_info(), expected


def nested_function() -> Result_Expected:
    """ Nested function call. """

    def inner():
        """ Inner (nested) function. """
        return get_caller_info(frame_index=3)

    expected = CallerInfo(FILE, "nested_function", {})
    return inner(), expected


class ClassTestObject:
    """ Class used for housing more test objects. """

    # noinspection PyMethodMayBeStatic
    def method(self) -> Result_Expected:
        """ Method call. """
        expected = CallerInfo(FILE, "ClassTestObject.method", {})
        return get_caller_info(), expected

    @classmethod
    def classmethod(cls) -> Result_Expected:
        """ Class method call. """
        expected = CallerInfo(FILE, "ClassTestObject.classmethod", {})
        return get_caller_info(), expected

    @staticmethod
    def staticmethod() -> Result_Expected:
        """ Static method call. """
        expected = CallerInfo(FILE, "staticmethod", {})
        return get_caller_info(), expected

    class NestedClass:
        """ Nest class definition. """

        # noinspection PyMethodMayBeStatic
        def method(self) -> Result_Expected:
            """ Method call within nested class definition. """
            expected = CallerInfo(FILE, "ClassTestObject.NestedClass.method", {})
            return get_caller_info(), expected


# ===== Tests ==============================================


@pytest.mark.parametrize(
    "function",
    [
        single_function_no_args,
        single_function_with_args,
        nested_function,
        ClassTestObject().method,
        ClassTestObject.classmethod,
        ClassTestObject.staticmethod,
        ClassTestObject.NestedClass().method,
    ],
)
def test_caller_function_inspection(function: Callable[..., Result_Expected]):
    # Arrange

    # Act
    result, expected = function()

    # Assert
    assert result == expected
