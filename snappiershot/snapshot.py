"""
Snapshot object, metadata and related functionality
"""
from typing import Any, Optional

from .compare import ObjectComparison
from .config import Config
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
                f"Expected a string value for the user_provided_name metadata field; "
                f"Found: {self.user_provided_name} of type {type(self.user_provided_name)}"
            )

        # Validate test_runner_provided_name
        if not isinstance(self.test_runner_provided_name, str):
            raise TypeError(
                f"Expected a string value for the test_runner_provided_name metadata field; "
                f"Found: {self.test_runner_provided_name} of type {type(self.test_runner_provided_name)}"
            )


class Snapshot:
    """Snapshot of a single assert value"""

    def __init__(self, configuration: Optional[Config] = None) -> None:
        """ Initialize snapshot associated with a particular assert """
        self.configuration = configuration if configuration is not None else Config()

    def assert_match(self, value: Any, exact: bool = False, update: bool = False) -> bool:
        """ Assert that the given value matches the snapshot on file

        Args:
            value: new value to compare to snapshot
            exact: if True, enforce exact equality for floating point numbers, otherwise assert approximate equality
            update: if True, overwrite snapshot with given value (assertion will always pass in this case)

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
        # Gather current snapshot metadata and value
        metadata = self._get_metadata()
        stored_value = self._get_value()

        # Encode the user-supplied value
        encoded_value = self._encode_value(value)

        # Update or assert the encoded snapshot value
        if metadata.update_on_next_run or update:
            # TODO: Implement snapshot overwriting
            # TODO: Impelement warning if "update" is on
            self._update_snapshot(new_value=encoded_value)
            return True

        ObjectComparison("a", 3.14, self.configuration)

        comparison = ObjectComparison(
            value=encoded_value,
            expected=stored_value,
            config=self.configuration,
            exact=exact,
        )
        if not comparison.equal:
            # TODO customize assertion error
            raise AssertionError
        return True

    @staticmethod
    def _get_metadata() -> SnapshotMetadata:
        """Gather metadata via inspection of current context

        TODO: Implement
        """

    @staticmethod
    def _get_value() -> Any:
        """ Gather stored snapshot value

        TODO: Implement
        """

    @staticmethod
    def _encode_value(value: Any) -> Any:
        """Encode the given object for snapshotting
        TODO: Implement
        """
        return value

    def _update_snapshot(self, new_value: Any) -> None:
        """Update the snapshot with the new encoded value

        TODO: Implement
        """
