"""
Snapshot object, metadata and related functionality
"""
from typing import Any

from .inspection import CallerInfo


class SnapshotMetadata:
    """Metadata associated with a single snapshot"""

    def __init__(
        self,
        caller_info: CallerInfo,
        update_on_next_run: bool,
        test_runner_provided_name: str = "",
        user_provided_name: str = "",
    ):
        """

        Args:
            caller_info: information about the calling test function
            update_on_next_run: if True, update snapshot value on next run
            test_runner_provided_name: string name of snapshot provided automatically by the test runner
            user_provided_name: user-provided name of the snapshot
        """
        self.caller_info = caller_info
        self.update_on_next_run = update_on_next_run
        self.user_provided_name = user_provided_name
        self.test_runner_provided_name = test_runner_provided_name
        self._validate()

    def _validate(self) -> None:
        """ Validates the snapshot metadata

        Raises:
            TypeError: If a metadata field has an invalid type.
        """
        # Validate caller_info
        if not isinstance(self.caller_info, CallerInfo):
            raise TypeError(
                f"Expected a CallerInfo object for the caller_info metadata field; "
                f"Found: {self.caller_info} of type {type(self.caller_info)}"
            )

        # Validate update_on_next_run
        if not isinstance(self.update_on_next_run, bool):
            raise TypeError(
                f"Expected a boolean value for the update_on_next_run metadata field; "
                f"Found: {self.update_on_next_run} of type {type(self.update_on_next_run)}"
            )

        # Validate user_provided_name
        if not isinstance(self.user_provided_name, str):
            raise TypeError(
                f"Expected a string value for the update_on_next_run metadata field; "
                f"Found: {self.user_provided_name} of type {type(self.user_provided_name)}"
            )

        # Validate test_runner_provided_name
        if not isinstance(self.test_runner_provided_name, str):
            raise TypeError(
                f"Expected a string value for the update_on_next_run metadata field; "
                f"Found: {self.test_runner_provided_name} of type {type(self.test_runner_provided_name)}"
            )


class Snapshot:
    """Snapshot of a single assert value"""

    def __init__(self) -> None:
        """ Initialize snapshot associated with a particular assert """
        self.metadata: SnapshotMetadata = self._get_metadata()
        self.value: Any = self._get_value()

    @staticmethod
    def _get_metadata() -> SnapshotMetadata:
        """Gather metadata via inspection of current context

        TODO: Implement
        """
        return SnapshotMetadata(
            caller_info=CallerInfo.from_call_stack(), update_on_next_run=False
        )

    @staticmethod
    def _get_value() -> Any:
        """ Gather stored snapshot value

        TODO: Implement
        """
        return None

    def assert_match(self, value: Any, exact: bool = False) -> bool:
        """ Assert that the given value matches the snapshot on file

        Args:
            value: new value to compare to snapshot
            exact: if True, enforce exact equality for floating point numbers, otherwise assert approximate equality

        Returns:
            True if value matches the snapshot

        Raises:
            AssertionError

        Example:
            >>> snapshot = Snapshot()
            >>> x = 1
            >>> y = 2
            >>> result = x + y
            >>> snapshot.assert_match(result)

        """
        if self.metadata.update_on_next_run:
            # TODO: Implement snapshot overwriting
            self._update_snapshot(value=value)
            return True

        if self.value == value:
            # TODO: Implement approximate vs exact equality
            return True

        # TODO customize assertion error
        raise AssertionError

    def _update_snapshot(self, value: Any) -> None:
        """Update the snapshot with the new value

        TODO: Implement
        """
