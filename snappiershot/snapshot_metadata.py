"""
Snapshot metadata
"""
from types import ModuleType, MethodType
from typing import Any, Tuple, Optional


class SnapshotMetadata:
    """Metadata associated with a single snapshot"""

    def __init__(
            self,
            test_module: ModuleType,
            test_class: Optional[type],
            test_method: MethodType,
            test_arguments: Tuple[str, Any],
            assert_index: int,
            update_on_next_run: bool
    ):
        """

        Args:
            test_module: test module
            test_class: test class or None if no test class
            test_method: test method
            test_arguments: tuple of argument names and values supplied to the test method
            assert_index: index of assert statement within test method
            update_on_next_run: if True, update snapshot value on next run
        """
        self.test_module = test_module
        self.test_class = test_class
        self.test_method = test_method
        self.test_arguments = test_arguments
        self.assert_index = assert_index
        self.update_on_next_run = update_on_next_run
