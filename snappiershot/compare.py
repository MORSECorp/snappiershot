""" Comparison of snapshots. """
from math import isclose, isnan
from operator import itemgetter
from typing import Any, Callable, Collection, Dict, Iterable, List, Tuple

from .config import Config


class SnapshotCompare:
    """ Class for comparing two objects and logging differences between them. """

    def __init__(self, value: Any, expected: Any, config: Config, exact: bool = False):
        """
        Args:
            value: The object to be checked.
            expected: The object to be compared against.
            config: Configurations used for performing the comparison.
            exact: Whether to **not** perform almost-equals comparison of floating point numbers.
        """
        self.value = value
        self.expected = expected
        self.config = config
        self.exact = exact
        self.differences = _SnapshotDifferences()
        self._compare(self.value, self.expected, operations=[])

    def __bool__(self) -> bool:
        """ Returns True if no differences were detected. """
        return not bool(self.differences.items)

    def _compare(self, value: Any, expected: Any, *, operations: List[Callable]) -> None:
        """ Perform a recursive, almost-equals comparison between value and expected.

        Args:
            value: The object to be checked.
            expected: The object to be compared against.
            operations: **Internally used for recursion**
              Tracks the operations that need to be applied to self.value and self.expected
                to obtain value and expected, respectively. Used for logging differences.
        """
        # Check the types of both objects.
        if type(value) != type(expected):
            message = f"Types not equal: {type(value)} != {type(expected)}"
            return self.differences.add(operations, message)

        if isinstance(value, dict):
            return self._compare_dicts(value, expected, operations=operations)

        # Compare unordered iterable types.
        if isinstance(value, set):
            return self._compare_sets(value, expected, operations=operations)

        # Recurse all other (ordered & sized) iterable types (but not strings).
        if isinstance(value, Collection) and not isinstance(value, str):
            return self._compare_collections(value, expected, operations=operations)

        if isinstance(value, float) and not self.exact:
            return self._compare_floats(value, expected, operations=operations)

        # Default to exact comparison for all other types.
        if value != expected:
            return self.differences.add(operations, f"{value} != {expected}")

    def _compare_collections(
        self, value: Any, expected: Any, *, operations: List[Callable] = None
    ) -> None:
        """ Perform a recursive, almost-equals comparison between value and expected.

        This is a helper function for when both value and expected are collections
          (ordered iterables).

        Args:
            value: The object to be checked.
            expected: The object to be compared against.
            operations: **Internally used for recursion**
              Tracks the operations that need to be applied to self.value and self.expected
                to obtain value and expected, respectively. Used for logging differences.
        """
        if len(value) != len(expected):
            message = (
                f"Collections do not have the same size: "
                f"{len(value)} != {len(expected)}"
            )
            return self.differences.add(operations, message)

        for index in range(len(value)):
            self._compare(
                value=value[index],
                expected=expected[index],
                operations=(operations + [itemgetter(index)]),
            )

    def _compare_dicts(
        self, value: Dict, expected: Dict, *, operations: List[Callable] = None
    ) -> None:
        """ Perform a recursive, almost-equals comparison between value and expected.

        This is a helper function for when both value and expected are dictionaries.

        Args:
            value: The object to be checked.
            expected: The object to be compared against.
            operations: **Internally used for recursion**
              Tracks the operations that need to be applied to self.value and self.expected
                to obtain value and expected, respectively. Used for logging differences.
        """
        if value.keys() != expected.keys():
            extra = value.keys() - expected.keys()
            missing = expected.keys() - value.keys()
            message = f"Dictionary keys do not match. Missing: {missing}; Extra: {extra}"
            return self.differences.add(operations, message)

        for key in value:
            self._compare(
                value=value[key],
                expected=expected[key],
                operations=(operations + [itemgetter(key)]),
            )

    def _compare_floats(
        self, value: Any, expected: Any, *, operations: List[Callable] = None
    ) -> None:
        """ Perform an almost-equals comparison between value and expected.

        This is a helper function for when both value and expected are floats.

        Special care is taken with NaN values and no errors are logged when both
          value and expected are NaN.

        Args:
            value: The object to be checked.
            expected: The object to be compared against.
            operations: **Internally used for recursion**
              Tracks the operations that need to be applied to self.value and self.expected
                to obtain value and expected, respectively. Used for logging differences.
        """
        # Specifically check if both values are NaN.
        if isnan(value) and isnan(expected):
            return

        rel_tol, abs_tol = self.config.rel_tol, self.config.abs_tol
        if not isclose(value, expected, rel_tol=rel_tol, abs_tol=abs_tol):
            message = (
                f"Floats not almost equal ({value} != {expected}). "
                f"Relative tolerance: {rel_tol} "
                f"Absolute tolerance: {abs_tol} "
            )
            return self.differences.add(operations, message)

    def _compare_sets(
        self, value: Any, expected: Any, *, operations: List[Callable] = None
    ) -> None:
        """ Perform an exact-equals comparison between value and expected.

        This is a helper function for when both value and expected are sets.

        Note: Currently this function does not perform almost-equals comparison
          between individual items within sets.

        Args:
            value: The object to be checked.
            expected: The object to be compared against.
            operations: **Internally used for recursion**
              Tracks the operations that need to be applied to self.value and self.expected
                to obtain value and expected, respectively. Used for logging differences.
        """
        if value != expected:
            extra = value - expected
            missing = expected - value
            reason = f"Sets do not match. Missing: {missing}; Extra: {extra}"
            return self.differences.add(operations, reason)


class _SnapshotDifferences:
    """ Helper object for logging comparisons for the SnapshotCompare class. """

    def __init__(self) -> None:
        self.items: Dict[Tuple[Callable, ...], str] = dict()

    def add(self, operations: Iterable[Callable], message: str) -> None:
        """ Add a difference to the log of differences.

        Args:
            operations: The operations that need to be applied to complex object to obtain
              the sub-object for which this difference is being logged.
            message: An explanatory message.
        """
        self.items[tuple(operations)] = message
