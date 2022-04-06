""" Metadata object used to identity and track snapshots. """
from typing import Any, Dict

from numpy import all, ndarray

from ..inspection import CallerInfo


def compare_metadata(from_test_function: Any, from_snapshot: Any) -> bool:
    """Instantiate object from a dictionary read from file in order to compare to SnappierShot input.

    SnappierShot serializes class objects by decomposing them into their parts in the form of a dictionary, then
    writes to the snapshot JSON. Thus, SnappierShot must attempt to re-instantiate the dictionary form of the
    objects when comparing inputs to a test function to the stored metadata inputs already serialized to snapshot JSON.

    Args:
        from_test_function: Inputs to the test function calling SnappierShot
        from_snapshot: Inputs to the test function after being serialized to JSON
    """
    result = False

    # Determine if the metadata can instantiate a class from a dictionary
    metadata_function_has_method = hasattr(from_test_function, "from_dict")

    if isinstance(from_test_function, ndarray) or isinstance(from_snapshot, ndarray):
        # If at least one is a numpy array, elementwise comparison can be done like this:
        result = all(from_test_function == from_snapshot)
    elif type(from_test_function) == type(from_snapshot):
        # If object types match, directly compare them
        result = from_test_function == from_snapshot
    elif (
        # Otherwise, if neither object is none and an object can be instantiated from a dictionary, do so
        metadata_function_has_method
        and from_test_function is not None
        and from_snapshot is not None
    ):
        result = from_test_function == from_test_function.from_dict(from_snapshot)

    return result


class SnapshotMetadata:
    """Metadata associated with a single snapshot."""

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
        """Returns a JSON-serializable dictionary of metadata."""
        dct = vars(self).copy()
        dct["arguments"] = dct.pop("caller_info").args
        return dct

    def matches(self, metadata_dict: Dict) -> bool:
        """Check if the "metadata" section of a snapshot file sufficiently matches
        the metadata object coming from the test method inputs.

        This matching is used to identify snapshots of tests within a snapshot file.

        Args:
            metadata_dict: The "metadata" section to compare against this object.
        """
        # Loop through every value in the metadata dictionary
        metadata_args = self.caller_info.args
        for key in metadata_args.keys():
            # Initialize objects
            inputs_from_test_method = metadata_args.get(key)
            inputs_from_file = metadata_dict["arguments"].get(key)

            if not compare_metadata(inputs_from_test_method, inputs_from_file):
                # Early exit if objects arent equal
                return False

        # If it made it through the checks, the objects are equal
        return True

    def _validate(self) -> None:
        """Validates the snapshot metadata.

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
