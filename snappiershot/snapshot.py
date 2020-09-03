"""
Snapshot object, metadata and related functionality
"""
from typing import Any

from .config import Config
from .inspection import CallerInfo


class SnapshotMetadata:
    """Metadata associated with a single snapshot"""

    def __init__(
            self,
            caller_info: CallerInfo,
            update_on_next_run: bool,
            test_runner_provided_name: str = "",
            user_provided_name: str = ""
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
            ValueError: If a configuration has an invalid value.
            TypeError: If a configuration has an invalid type.
        """
        # Validate caller_info
        if not isinstance(self.caller_info, CallerInfo):
            raise TypeError(
                f"Expected a CallerInfo object for the update_on_next_run metadata field; "
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

    def __init__(self, configuration: Config):
        """Initialize snapshot associated with a particular assert
        Args:
            configuration: Snappiershot configuration
        """
        self.configuration = configuration
        self.metadata: SnapshotMetadata = SnapshotMetadata()  # TODO: Gather metadata via inspection of test context
        self.value: Any = None

    def assert_match(self, value: Any, approximate: bool = True) -> bool:
        """ Assert that the given value matches the snapshot on file

        Args:
            value: new value to compare to snapshot
            approximate: if True, assert approximate equality

        Returns:
            True if value matches the snapshot

        Raises:
            AssertionError
        """
        if self.metadata.update_on_next_run:
            # TODO: implement snapshot overwriting
            self._update_snapshot(value=value)
            return True

        if self.value == value:
            # TODO: Implement approximate equality
            return True

        # TODO customize assertion error
        raise AssertionError

    def _update_snapshot(self, value: Any) -> None:
        """Update the snapshot with the new value

        TODO: Implement
        """
