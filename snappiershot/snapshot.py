"""
Snapshot object
"""
from typing import Any

from .snapshot_metadata import SnapshotMetadata
from .config import Config
from . import exceptions as custom_errors


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


class SnapshotModule:
    """Collect and organize all snapshots associated with a single test module"""

    def __init__(self):
        """Initialize new collection of snapshots"""
        self.snapshots = dict()

    def add_snapshot(self, snapshot: Snapshot) -> None:
        """Add the given snapshot to the stored snapshots

        Snapshots are stored as a hierarchical dictionary organized by module, class, method
            function iteration, and assert statement

        Args:
            snapshot: snapshot object to add to the store
        """

        # By test module
        test_module = snapshot.metadata.test_module
        if test_module not in self.snapshots:
            self.snapshots[test_module] = dict()

        # By test class
        module_dict = self.snapshots[test_module]
        test_class = snapshot.metadata.test_class
        if test_class not in module_dict:
            module_dict[test_class] = dict()

        # By test method
        class_dict = module_dict[test_class]
        test_method = snapshot.metadata.test_method
        if test_method not in class_dict:
            class_dict[test_method] = dict()

        # By test arguments (method call)
        method_dict = class_dict[test_method]
        test_args = snapshot.metadata.test_arguments
        if test_args not in method_dict:
            method_dict[test_args] = dict()

        # By assert index - Store snapshot
        function_call_dict = method_dict[test_args]
        assert_index = snapshot.metadata.assert_index
        function_call_dict[assert_index] = snapshot

    def get_snapshot(self, metadata: SnapshotMetadata) -> Snapshot:
        """Look up and return snapshot based on given metadata

        Args:
            metadata: snapshot metadata

        Returns:
            Stored snapshot associated with the given metadata

        Raises:
            SnapshotNotFoundError is requested snapshot is not available
        """
        try:
            return self.snapshots[
                metadata.test_module
            ][
                metadata.test_class
            ][
                metadata.test_method
            ][
                metadata.test_arguments
            ][
                metadata.assert_index
            ]

        except AttributeError:
            raise custom_errors.SnapshotNotFoundError

