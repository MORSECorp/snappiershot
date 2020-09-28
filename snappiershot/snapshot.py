"""
Snapshot object, metadata and related functionality
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .compare import ObjectComparison
from .config import Config
from .inspection import CallerInfo
from .serializers import JsonDeserializer, JsonSerializer
from .serializers.utils import get_snapshot_file

_NO_SNAPSHOT = object()


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

    def matches(self, metadata_dict: Dict) -> bool:
        """ Check if the "metadata" section of a snapshot file sufficiently matches
        this metadata object.

        This matching is used to identify snapshots of tests within a snapshot file.

        Args:
            metadata_dict: The "metadata" section to compare against this object.
        """
        return self.caller_info.args == metadata_dict["arguments"]

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
        self._snapshot_index = 0

        # These are loaded on first call to the assert_math method.
        self._metadata: Optional[SnapshotMetadata] = None
        self._snapshot_file: Optional[_SnapshotFile] = None

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
            >>> x = 1
            >>> y = 2
            >>> result = x + y
            >>> with Snapshot() as snapshot:
            >>>     snapshot.assert_match(result)
        """
        self._metadata = self._get_metadata(update_on_next_run=update)
        self._snapshot_file = self._load_snapshot_file(metadata=self._metadata)

        # Get the stored value from the snapshot file and increment the snapshot counter.
        current_index = self._snapshot_index
        stored_value = self._snapshot_file.get_snapshot(current_index)
        self._snapshot_index += 1

        # Encode the user-supplied value
        encoded_value = self._encode_value(value)

        # Overwrite the snapshot value.
        if self._metadata.update_on_next_run or (stored_value is _NO_SNAPSHOT):
            # TODO: Implement warning if "update" is on
            self._snapshot_file.record_snapshot(encoded_value, current_index)
            return True

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

    def __enter__(self) -> "Snapshot":  # pragma: no cover  TODO: Cover
        """ Enter the context of a Snapshot session. """
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover  TODO: Cover
        """ Exits the context of the Snapshot session. """
        if self._snapshot_file is not None:
            self._snapshot_file.write()

    @staticmethod
    def _encode_value(value: Any) -> Any:
        """Encode the given object for snapshotting
        TODO: Implement
        """
        return value

    def _get_metadata(
        self, update_on_next_run: bool
    ) -> SnapshotMetadata:  # pragma: no cover  TODO: Cover
        """ Gather metadata via inspection of current context.

        A SnapshotMetadata object is created only if self._metadata is not already set.
        However, the "update_on_next_run" attribute is set every time.

        Args:
            update_on_next_run: Setting for SnapshotMetadata.update_on_next_run
        """
        if isinstance(self._metadata, SnapshotMetadata):
            self._metadata.update_on_next_run = update_on_next_run
            return self._metadata
        caller_info = CallerInfo.from_call_stack(frame_index=3)
        return SnapshotMetadata(
            caller_info=caller_info, update_on_next_run=update_on_next_run
        )

    def _load_snapshot_file(
        self, metadata: SnapshotMetadata
    ) -> "_SnapshotFile":  # pragma: no cover  TODO: Cover
        """ Load the snapshot file into memory.

        The snapshot file is only loaded if self._snapshot_file is not already set.

        Args:
            metadata: The SnapshotMetadata object used to identify the correct snapshots.
        """
        if isinstance(self._snapshot_file, _SnapshotFile):
            return self._snapshot_file
        return _SnapshotFile(config=self.configuration, metadata=metadata)


class _SnapshotFile:
    """ Reads and Writes a snapshot file.

    Format:
        {
            "snappiershot_version": "0.1.0",
            "tests": {
                "fully_qualified_name_to_test_function_1": [
                    {
                        "metadata": {
                            "user_provided_name": "",
                            "test_runner_provided_name": "",
                            "update_on_next_run: False,
                            "arguments": {
                                "argument_name_1": "argument_value_1",
                                "argument_name_2": "argument_value_2"
                            }
                        },
                        "snapshots": [
                            { ... first snapshot of test_1 ... },
                            { ... second snapshot of test_1 ... }
                        ]
                    }
                ],
                "fully_qualified_name_to_test_function_2": [
                    {
                        "metadata": {
                            "user_provided_name": "",
                            "test_runner_provided_name": "",
                            "update_on_next_run: False,
                            "arguments": {
                                "argument_name_1": "argument_value_1",
                                "argument_name_2": "argument_value_2"
                            }
                        },
                        "snapshots": [
                            { ... first snapshot of test_2 ... },
                            { ... second snapshot of test_2 ... }
                        ]
                    }
                ]
            }
        }
    """

    def __init__(self, config: Config, metadata: SnapshotMetadata):
        """
        Args:
            config: The snappiershot configurations.
            metadata: The SnapshotMetadata used for identifying snapshots.
        """
        self.config = config
        self.metadata = metadata

        # The path to the snapshot file.
        self._snapshot_file = self._get_snapshot_file(
            test_file=self.metadata.caller_info.file, file_format=self.config.file_format
        )
        # The parsed contents of the snapshot file.
        self._file_contents = self._parse_snapshot_file(self._snapshot_file)
        # The snapshots the correspond with the test function.
        self._snapshots = self._find_snapshots(self._file_contents, self.metadata)
        # True if any changes have been made to the snapshot file.
        self._changed_flag = False

    def get_snapshot(self, index: int = 0) -> Union[Dict, object]:
        """ Return a snapshot from the snapshot file.

        This snapshot will correspond to the test function.
        If no snapshot exists for the specified index, returns _NO_SNAPSHOT
          (not None since "None" is a valid snapshot value).

        Args:
            index: The index of the snapshot to return (tests can snapshot multiple items).
        """
        try:
            return self._snapshots[index]
        except IndexError:
            return _NO_SNAPSHOT

    def record_snapshot(self, value: Any, index: int = -1) -> None:
        """ Record a snapshot for the test function.

        Args:
            value: The snapshot value to record.
            index: The index of the snapshot to record (tests can snapshot multiple items).
        """
        self._changed_flag = True
        index = len(self._snapshots) if index == -1 else index
        self._snapshots.insert(index, value)

    def write(self) -> None:
        """ Write out the snapshots.

        Raises:
            ValueError: If the file format of the snapshot_file is not recognized.
        """
        if not self._changed_flag:
            return
        if self._snapshot_file.suffix == ".json":
            with self._snapshot_file.open("w") as snapshot_file:
                json.dump(
                    obj=self._file_contents,
                    fp=snapshot_file,
                    cls=JsonSerializer,
                    indent=self.config.json_indentation,
                    sort_keys=True,
                )
        else:  # pragma: no cover
            raise ValueError(
                f"Snapshot file format not supported: {self._snapshot_file.suffix}"
            )

    @property
    def _empty_file_contents(self) -> Dict:
        """ Returns the contents of an empty snapshot file.

        This value is used if a snapshot file does not exist.
        This needs to be within a property to avoid circular import limitations.
        """
        import snappiershot

        return dict(snappiershot_version=snappiershot.__version__, tests=dict())

    @staticmethod
    def _find_snapshots(file_contents: Dict, metadata: SnapshotMetadata) -> List[Dict]:
        """ Finds the snapshots that correspond to the test function.

        Will return an empty list of no snapshots are found.

        Args:
            file_contents: The contents of the snappiershot file.
        """

        if metadata.caller_info.function not in file_contents["tests"]:
            file_contents["tests"][metadata.caller_info.function] = []
        function_snapshots = file_contents["tests"][metadata.caller_info.function]

        for function_snapshot in function_snapshots:
            metadata_dict = function_snapshot["metadata"]
            if metadata.matches(metadata_dict):
                metadata.update_on_next_run |= metadata_dict["update_on_next_run"]
                metadata_dict["update_on_next_run"] = False
                return function_snapshot["snapshots"]

        function_snapshots.append(
            dict(
                metadata=dict(
                    user_provided_name=metadata.user_provided_name,
                    test_runner_provided_name=metadata.test_runner_provided_name,
                    update_on_next_run=False,
                    arguments=metadata.caller_info.args,
                ),
                snapshots=[],
            )
        )
        return function_snapshots[-1]["snapshots"]

    @staticmethod
    def _get_snapshot_file(test_file: Path, file_format: str) -> Path:
        """ Locates the snapshot file for the correct file format.

        Args:
            test_file: The path to the test file associated with the snapshot file.
            file_format: The file format for the snapshot file.

        Raises:
            ValueError: If the file_format is not recognized.
        """
        if file_format == "JSON":
            return get_snapshot_file(test_file=test_file, suffix=".json")
        raise ValueError(f"Snapshot file format not supported: {file_format}")

    def _parse_snapshot_file(self, snapshot_file: Path) -> Dict:
        """ Parses the snapshot file.

        Args:
            snapshot_file: The path to the file containing snapshots.

        Raises:
            ValueError: If the file format of the snapshot_file is not recognized.
        """
        if not snapshot_file.exists():
            return self._empty_file_contents
        if snapshot_file.suffix == ".json":
            with snapshot_file.open() as json_file:
                file_contents = json.load(json_file, cls=JsonDeserializer)
        else:  # pragma: no cover  (unreachable)
            raise ValueError(f"Snapshot file format not supported: {snapshot_file.suffix}")

        if not (("snappiershot_version" in file_contents) and ("tests" in file_contents)):
            raise ValueError(
                f"Invalid snapshot file detected: {snapshot_file} \n"
                f"Expected contents: {self._empty_file_contents}"
            )
        return file_contents
