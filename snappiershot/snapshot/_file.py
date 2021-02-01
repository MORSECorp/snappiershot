""" Interface for the snapshot files. """
from pathlib import Path
from typing import Any, Dict, List, Union, cast

from ..config import Config
from ..constants import SnapshotKeys
from ..serializers.io import parse_snapshot_file, write_json_file
from ..serializers.utils import default_encode_value, get_snapshot_file
from .metadata import SnapshotMetadata
from .status import SnapshotStatus

_NO_SNAPSHOT = object()


class _SnapshotFile:
    """ Reads and Writes a snapshot file.

    This class performs the following actions at initialization:
        1. Locates the snapshot file associated with the test function
            that called Snapshot.assert_match.
        2. Parses the snapshot file (validates the format described below).
        3. Finds the snapshot within the parsed file that match the
            input SnapshotMetadata object.

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
            config: The snappiershot configuration.
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
        # The status for the individual snapshots.
        self._snapshot_statuses = [SnapshotStatus.UNCHECKED for _ in self._snapshots]

    def get_snapshot(self, index: int) -> Union[Dict, object]:
        """ Return a snapshot from the snapshot file.

        This snapshot will correspond to the test function, with the index
          corresponding to the nth assertion made by the test function.
        If no snapshot exists for the specified index, returns _NO_SNAPSHOT
          (not None since "None" is a valid snapshot value).

        Args:
            index: The index of the snapshot to return (tests can snapshot multiple items).
        """
        try:
            return self._snapshots[index]
        except IndexError:
            return _NO_SNAPSHOT

    def mark_failed(self, index: int) -> None:
        """ Set the status for the snapshot at the specified index as "FAILED". """
        self._mark_snapshot_status(index, SnapshotStatus.FAILED)

    def mark_passed(self, index: int) -> None:
        """ Set the status for the snapshot at the specified index as "PASSED". """
        self._mark_snapshot_status(index, SnapshotStatus.PASSED)

    def record_snapshot(self, value: Any, index: int = -1) -> None:
        """ Record a snapshot for the test function.

        Marks the snapshot at the given index as "RECORDED".

        Args:
            value: The snapshot value to record.
            index: The index of the snapshot to record (tests can snapshot multiple items).
        """
        self._changed_flag = True
        index = len(self._snapshots) if index == -1 else index
        if index >= len(self._snapshots):
            self._snapshots.append(value)
        else:
            self._snapshots[index] = value
        self._mark_snapshot_status(index, SnapshotStatus.RECORDED)

    def write(self) -> None:
        """ Write out the snapshots.

        Raises:
            ValueError: If the file format of the snapshot_file is not recognized.
        """
        if not self._changed_flag:
            return
        if self._snapshot_file.suffix == ".json":
            write_json_file(
                obj=self._file_contents,
                file=self._snapshot_file,
                indent=self.config.json_indentation,
            )
        else:  # pragma: no cover
            raise ValueError(
                f"Unsupported snapshot file format: {self._snapshot_file.suffix}"
            )

        # Change all "Recorded" statuses to "Written".
        for index in range(len(self._snapshot_statuses)):
            if self._snapshot_statuses[index] == SnapshotStatus.RECORDED:
                self._snapshot_statuses[index] = SnapshotStatus.WRITTEN

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
        # Checks to see if the section exists within the snapshot file for the test function.
        #   If not, then one is created.
        function_name = metadata.caller_info.function
        if function_name not in file_contents[SnapshotKeys.tests]:
            file_contents[SnapshotKeys.tests][function_name] = []
        function_snapshots = file_contents[SnapshotKeys.tests][function_name]

        # Tries to locate the sub-section of the snapshot file with matching metadata section.
        for function_snapshot in function_snapshots:
            metadata_dict = function_snapshot[SnapshotKeys.metadata]
            if metadata.matches(metadata_dict):
                metadata.update_on_next_run |= metadata_dict[SnapshotKeys.update]
                metadata_dict[SnapshotKeys.update] = False
                return function_snapshot[SnapshotKeys.snapshots]

        # If no sub-section exists, create it.
        encoded_metadata = cast(dict, default_encode_value(metadata.as_dict(), set()))
        function_snapshots.append(
            dict(metadata={**encoded_metadata, "update_on_next_run": False}, snapshots=[])
        )
        return function_snapshots[-1][SnapshotKeys.snapshots]

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
        raise ValueError(f"Unsupported snapshot file format: {file_format}")

    def _mark_snapshot_status(self, index: int, status: SnapshotStatus) -> None:
        """ Set the status for the snapshot at the specified index as the specified status.

        This will handle out-of-bounds indices.
        """
        if index >= len(self._snapshot_statuses):
            self._snapshot_statuses.append(status)
        else:
            self._snapshot_statuses[index] = status

    def _parse_snapshot_file(self, snapshot_file: Path) -> Dict:
        """ Parses the snapshot file.

        Args:
            snapshot_file: The path to the file containing snapshots.

        Raises:
            ValueError: If the file format of the snapshot_file is not recognized.
        """
        if not snapshot_file.exists():
            return self._empty_file_contents
        return parse_snapshot_file(snapshot_file)
