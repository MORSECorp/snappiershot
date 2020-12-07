""" Metadata object used to identity and track snapshots. """
from typing import Dict

from ..inspection import CallerInfo


class SnapshotMetadata:
    """ Metadata associated with a single snapshot. """

    def __init__(
        self,
        caller_info: CallerInfo,
        update_on_next_run: bool,
        test_runner_provided_name: str = "",
        user_provided_name: str = "",
    ):
        """
        Args:
            caller_info: Information about the calling test function.
            update_on_next_run: If True, update snapshot value on next run.
            test_runner_provided_name: String name of snapshot provided automatically
              by the test runner.
            user_provided_name: User-provided name of the snapshot.
        """
        self.caller_info = caller_info
        self.update_on_next_run = update_on_next_run
        self.user_provided_name = user_provided_name
        self.test_runner_provided_name = test_runner_provided_name
        self._validate()

    def as_dict(self) -> Dict:
        """ Returns a JSON-serializable dictionary of metadata. """
        dct = vars(self).copy()
        dct["arguments"] = dct.pop("caller_info").args
        return dct

    def matches(self, metadata_dict: Dict) -> bool:
        """ Check if the "metadata" section of a snapshot file sufficiently matches
        this metadata object.

        This matching is used to identify snapshots of tests within a snapshot file.

        Args:
            metadata_dict: The "metadata" section to compare against this object.
        """
        return self.caller_info.args == metadata_dict["arguments"]

    def _validate(self) -> None:
        """ Validates the snapshot metadata.

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
