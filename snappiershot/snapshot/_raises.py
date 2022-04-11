""" Context class used to track and snapshot raised exceptions.

Mimics and is inspired by `pytest.raises`.
"""
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

if TYPE_CHECKING:  # pragma: no cover
    # Used to avoid circular imports.
    from .snapshot import Snapshot

# Creates a Exception TypeVariable to be used for type-hinting.
_E = TypeVar("_E", bound=BaseException)
_ExceptionTypes = Union[Type[_E], Tuple[Type[_E], ...]]


class _RaisesContext(Generic[_E]):
    """Context class used to track and snapshot raised exceptions."""

    def __init__(
        self, snapshot: "Snapshot", expected_exceptions: _ExceptionTypes, update: bool
    ):
        """
        Args:
            snapshot: The snapshot object. Used to perform the actual snapshotting of the
              raised exception. This object must have the metadata preset.
            expected_exceptions: A tuple of exception types that are expected to be raised.
            update: Whether to update the snapshot or not.
        """
        self.snapshot = snapshot
        self.expected_exceptions = expected_exceptions
        self.update = update

        # Tracks whether the assertion was matched. Used for testing.
        self._assert_match = False

    def __enter__(self) -> "_RaisesContext":
        """Enter the context."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Exit the context, checking exception types (if raised) and snapshotting.

        Args:
            exc_type: The type of exception raised within the context (if exists).
            exc_val: The exception raised within the context (if exists).
            exc_tb: The traceback of the exception raised with the context (if exists).

        Raises:
            ValueError: If no exception was raised.
            TypeError: If an unexpected type was raised.
            AssertionError: If the exception does not match the snapshot.
        """
        if exc_type is None:
            raise ValueError("No exception raised. ")
        if not issubclass(exc_type, self.expected_exceptions):
            raise TypeError(
                f"Expected exception of type(s): {self.expected_exceptions}"
                f" -- Found {exc_type}"
            )
        self._assert_match = self.snapshot.assert_match(exc_val, update=self.update)

        # Note: It is important that this value is returned, as an ``object.__exit__``
        #   method returning True indicates that any exception raised while within
        #   context is suppressed, as is necessary when the assertion matches.
        return self._assert_match
