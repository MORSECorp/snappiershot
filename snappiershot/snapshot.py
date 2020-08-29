"""
Snapshot object
"""
from typing import Any

from .snapshot_metadata import SnapshotMetadata
from .config import Config


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

    def assert_match(self, value: Any, approximate: bool) -> bool:
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




