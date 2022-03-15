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
        # If this dictionary can instantiate into a class, do it.
        metadata_args = self.caller_info.args
        dict_to_compare: dict = {}
        for key in metadata_args.keys():
            dict_to_compare[key] = None
            metadata_obj = metadata_args.get(key)
            dict_from_file = metadata_dict["arguments"].get(key)

            metadata_obj_has_method = hasattr(metadata_obj, "from_dict")
            metadata_obj_is_not_none = metadata_obj is not None
            dict_from_file_is_not_none = dict_from_file is not None

            if isinstance(metadata_obj, list) and isinstance(dict_from_file, list):
                dict_to_compare[key] = list()
                for kk in range(len(metadata_obj)):
                    ii = metadata_obj[kk]
                    jj = dict_from_file[kk]

                    metadata_obj_has_method = hasattr(ii, "from_dict")
                    metadata_obj_is_not_none = ii is not None
                    dict_from_file_is_not_none = jj is not None

                    if type(ii) == type(jj):
                        dict_to_compare[key].append(jj)
                    elif (
                        metadata_obj_has_method
                        and metadata_obj_is_not_none
                        and dict_from_file_is_not_none
                    ):
                        dict_to_compare[key].append(ii.from_dict(jj))
            else:
                if type(metadata_obj) == type(dict_from_file):
                    dict_to_compare[key] = dict_from_file
                elif (
                    metadata_obj_has_method
                    and metadata_obj_is_not_none
                    and dict_from_file_is_not_none
                ):
                    dict_to_compare[key] = metadata_obj.from_dict(dict_from_file)

        return metadata_args == dict_to_compare

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
