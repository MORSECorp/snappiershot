""" Functionality for tracking the status of snapshot files throughout testing.

The underlying data format of tracker largely follows the structure of
  the snapshot (JSON) file format:
 {
   <path-to-snapshot-file>: {
     <test_function_name>: [
       {
         metadata: <metadata-dictionary>
         snapshots: [ <SnapshotStatus object for each snapshot.assert_match> ]
       },
       ...
     ],
     ...
   },
   ...
 }
"""
from pathlib import Path
from typing import Dict, List, NamedTuple

from snappiershot.constants import SNAPSHOT_DIRECTORY
from snappiershot.serializers.utils import SnapshotKeys, parse_snapshot_file
from snappiershot.snapshot import SnapshotMetadata, SnapshotStatus


class StatusReport(NamedTuple):
    """ NamedTuple for returning a status report for the snapshot testing session. """

    unchecked: int = 0
    failed: int = 0
    passed: int = 0
    recorded: int = 0
    written: int = 0

    def any(self) -> bool:
        """ Return a boolean that is False if all status reports are zero, else True. """
        return bool(
            self.unchecked or self.failed or self.passed or self.recorded or self.written
        )


class SnapshotTracker:
    """ Class used to track snapshot status throughout an entire test-run session. """

    def __init__(self, *paths: Path):
        """
        Args:
            paths: Testing paths that are to be searched recursively for snapshot files.
        """
        # Collect all (unique) snapshot files.
        self.snapshot_files = {
            file.resolve()
            for path in paths
            for directory in path.rglob(SNAPSHOT_DIRECTORY)
            for file in directory.glob(f"*.json")
        }
        self.snapshots = self._construct()

    def get_status_report(self) -> StatusReport:
        """ Return the status report. """
        unchecked = failed = passed = recorded = written = 0
        for file, functions in self.snapshots.items():
            for function_name, function_calls in functions.items():
                for function_call in function_calls:
                    for status in function_call["snapshots"]:
                        if status == SnapshotStatus.UNCHECKED:
                            unchecked += 1
                        elif status == SnapshotStatus.FAILED:
                            failed += 1
                        elif status == SnapshotStatus.PASSED:
                            passed += 1
                        elif status == SnapshotStatus.RECORDED:
                            recorded += 1
                        elif status == SnapshotStatus.WRITTEN:
                            written += 1
                        else:  # pragma: no cover
                            raise ValueError(f"Unknown snapshot status: {status}")
        return StatusReport(unchecked, failed, passed, recorded, written)

    def set_status(
        self,
        statuses: List[SnapshotStatus],
        snapshot_file: Path,
        function_name: str,
        metadata: SnapshotMetadata,
    ) -> None:
        """ Set the statuses an individual snapshot run.

        Args:
            statuses: The statuses of the snapshot files for a particular test function.
            snapshot_file: The path to the file containing the snapshots.
            function_name: The name of the test function that was run.
            metadata: The metadata associated with the test function that was run.
        """
        # Get the data for the snapshot file, create it if no data exists.
        if snapshot_file not in self.snapshots:
            self.snapshots[snapshot_file] = dict()
        snapshots = self.snapshots[snapshot_file]

        # Get the data for the test function, create it if no data exists.
        if function_name not in snapshots:
            snapshots[function_name] = list()
        function_snapshots = snapshots[function_name]

        # Update the snapshot statuses if the data exists.
        for function_snapshot in function_snapshots:
            metadata_dict = function_snapshot[SnapshotKeys.metadata]
            if metadata.matches(metadata_dict):
                function_snapshot[SnapshotKeys.snapshots] = statuses
                return

        # Append the snapshot statuses if the data does not exist.
        function_snapshots.append(dict(metadata=metadata.as_dict(), snapshots=statuses))

    def _construct(self) -> Dict:
        """ Construct the underlying data structure for tracking snapshots.

        This format of tracker largely follows the structure of
          the snapshot (JSON) file format:
         {
           <path-to-snapshot-file>: {
             <test_function_name>: [
               {
                 metadata: <metadata-dictionary>
                 snapshots: [ <SnapshotStatus object for each snapshot.assert_match> ]
               },
               ...
             ],
             ...
           },
           ...
         }
        """
        data_structure = dict()
        for snapshot_file in self.snapshot_files:
            try:
                parsed_file = parse_snapshot_file(snapshot_file)
            except ValueError:  # pragma: no cover
                # Ignore any unparsable files.
                continue

            # The tracker object only cares about statuses of the snapshots,
            #   not the contents.
            contents = parsed_file[SnapshotKeys.tests]
            for function_name, call_records in contents.items():
                for call_index, call_record in enumerate(call_records):
                    snapshots = call_record[SnapshotKeys.snapshots]
                    statuses = [SnapshotStatus.UNCHECKED for _ in snapshots]
                    contents[function_name][call_index][SnapshotKeys.snapshots] = statuses
            data_structure[snapshot_file] = contents
        return data_structure
