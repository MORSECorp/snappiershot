""" Metadata object used to identity and track snapshots. """
from typing import Any, Dict

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

    def compare_instantiated_objects(
        self, obj_from_metadata: Any, obj_from_snapshot_file: Any
    ) -> bool:
        """ Instantiate object from a dictionary read from file in order to compare to metadata.

        While encoding complex objects, an object decomposed into its parts in the form of a dictionary is written
        to the snapshot JSON. Thus, snappiershot must attempt to re-instantiate those objects to do a direct
        comparison.

        Args:
            obj_from_metadata: An object coming from the metadata.
            obj_from_snapshot_file: An object (or decomposed object in the form of a dictionary) read out of the
            snapshot file.
        """
        # Determine if the metadata object can instantiate a class from a dictionary, or whether any object is None
        metadata_obj_has_method = hasattr(obj_from_metadata, "from_dict")
        metadata_obj_is_not_none = obj_from_metadata is not None
        obj_from_file_is_not_none = obj_from_snapshot_file is not None

        result = False  # initialize result to false

        if type(obj_from_metadata) == type(obj_from_snapshot_file):
            # If object types match, directly compare them
            result = obj_from_metadata == obj_from_snapshot_file
        elif (
            # Otherwise, if neither object is none and an object can be instantiated from a dictionary, do so
            metadata_obj_has_method
            and metadata_obj_is_not_none
            and obj_from_file_is_not_none
        ):
            result = obj_from_metadata == obj_from_metadata.from_dict(
                obj_from_snapshot_file
            )

        return result

    def matches(self, metadata_dict: Dict) -> bool:
        """ Check if the "metadata" section of a snapshot file sufficiently matches
        this metadata object.

        This matching is used to identify snapshots of tests within a snapshot file.

        Args:
            metadata_dict: The "metadata" section to compare against this object.
        """
        # Loop through every value in the metadata dictionary
        metadata_args = self.caller_info.args
        for key in metadata_args.keys():
            # Initialize objects
            metadata_obj = metadata_args.get(key)
            dict_from_file = metadata_dict["arguments"].get(key)

            # If the object is a list, must loop through it and compare each index
            if isinstance(metadata_obj, list) and isinstance(dict_from_file, list):
                for kk in range(len(metadata_obj)):
                    if not self.compare_instantiated_objects(
                        metadata_obj[kk], dict_from_file[kk]
                    ):
                        # Early exit if objects arent equal
                        return False
            else:
                if not self.compare_instantiated_objects(metadata_obj, dict_from_file):
                    # Early exit if objects arent equal
                    return False

        # If it made it through the checks, the objects are equal
        return True

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
