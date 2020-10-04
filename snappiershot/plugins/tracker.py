""" Functionality for tracking the status of snapshot files throughout testing. """
from pathlib import Path
from typing import List

from snappiershot.serializers.utils import SnapshotKeys, parse_snapshot_file
from snappiershot.snapshot import SnapshotMetadata, SnapshotStatus


class Tracker:
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
            for directory in path.rglob(".snapshots")
            for file in directory.glob(f"*.json")
        }

        # Create a dictionary used to track snapshot assertions throughout an entire run.
        # The format:
        #  {
        #    <path-to-snapshot-file>: {
        #      <test_function_name>: [
        #        {
        #          metadata: <metadata-dictionary>
        #          snapshots: [ <SnapshotStatus object for each snapshot.assert_match> ]
        #        },
        #        ...
        #      ],
        #      ...
        #    },
        #    ...
        #  }
        self.snapshots = dict()
        for snapshot_file in self.snapshot_files:
            try:
                parsed_file = parse_snapshot_file(snapshot_file)
            except ValueError:  # pragma: no cover
                # Ignore any unparsable files.
                continue

            # The tracker object only cares about
            contents = parsed_file[SnapshotKeys.tests]
            for function_name, call_records in contents.items():
                for call_index, call_record in enumerate(call_records):
                    snapshots = call_record[SnapshotKeys.snapshots]
                    statuses = [SnapshotStatus.UNCHECKED for _ in snapshots]
                    contents[function_name][call_index][SnapshotKeys.snapshots] = statuses
            self.snapshots[snapshot_file] = contents

    def set_status(
        self,
        statuses: List[SnapshotStatus],
        snapshot_file: Path,
        function_name: str,
        metadata: SnapshotMetadata,
    ) -> None:
        """ Set the statuses an individual snapshot run. """
        if snapshot_file not in self.snapshots:
            self.snapshots[snapshot_file] = dict()
        snapshots = self.snapshots[snapshot_file]

        if function_name not in snapshots:
            snapshots[function_name] = list()
        function_snapshots = snapshots[function_name]

        for function_snapshot in function_snapshots:
            metadata_dict = function_snapshot[SnapshotKeys.metadata]
            if metadata.matches(metadata_dict):
                function_snapshot[SnapshotKeys.snapshots] = statuses
                return

        function_snapshots.append(dict(metadata=metadata.as_dict(), snapshots=statuses))
