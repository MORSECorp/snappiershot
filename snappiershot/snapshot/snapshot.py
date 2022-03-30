""" Snapshot object (the public API). """
import warnings
from difflib import Differ
from shutil import get_terminal_size
from typing import Any, List, Optional, Tuple

import pprint_ordered_sets as pprint

from ..compare import ObjectComparison
from ..config import Config
from ..errors import SnappierShotWarning
from ..inspection import CallerInfo
from ..serializers.utils import default_encode_value
from ._file import _NO_SNAPSHOT, _SnapshotFile
from ._raises import _ExceptionTypes, _RaisesContext
from .metadata import SnapshotMetadata


class Snapshot:
    """Snapshot of a single assert value"""

    def __init__(self, configuration: Optional[Config] = None) -> None:
        """Initialize snapshot associated with a particular assert"""
        self.configuration = configuration if configuration is not None else Config()
        self._snapshot_index = 0
        self._within_context = False

        # These are loaded on first call to the assert_math method.
        self._metadata: Optional[SnapshotMetadata] = None
        self._snapshot_file: Optional[_SnapshotFile] = None

    def assert_match(
        self, value: Any, exact: bool = False, update: bool = False, ignore: List[str] = []
    ) -> bool:
        """Assert that the given value matches the snapshot on file

        Args:
            value: new value to compare to snapshot
            exact: if True, enforce exact equality for floating point numbers,
              otherwise assert approximate equality
            update: if True, overwrite snapshot with given value
              (assertion will always pass in this case)
            ignore: if set, will ignore variables names from the metadata

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
        if not self._within_context:
            raise RuntimeError("assert_match must be used within the Snapshot context. ")

        self._metadata = self._get_metadata(
            update_on_next_run=update, args_to_ignore=ignore
        )
        self._snapshot_file = self._load_snapshot_file(metadata=self._metadata)

        # Get the stored value from the snapshot file and increment the snapshot counter.
        current_index = self._snapshot_index
        stored_value = self._snapshot_file.get_snapshot(current_index)
        self._snapshot_index += 1

        # Encode the user-supplied value
        encoded_value = default_encode_value(value)  # type: ignore

        # Overwrite the snapshot value.
        if self._metadata.update_on_next_run or (stored_value is _NO_SNAPSHOT):
            if update:
                warnings.warn(
                    "This snapshot was forced to update with update=True argument. "
                    "This is dangerous to have on for CI pipelines! ",
                    SnappierShotWarning,
                )
            self._snapshot_file.record_snapshot(encoded_value, current_index)
            return True

        comparison = ObjectComparison(
            value=encoded_value,
            expected=stored_value,
            config=self.configuration,
            exact=exact,
        )
        if not comparison.equal:
            self._snapshot_file.mark_failed(current_index)
            diff = self._construct_diff(encoded_value, stored_value, comparison)
            message = "Snapshot does not match:\n" + diff
            raise AssertionError(message)
        self._snapshot_file.mark_passed(current_index)
        return True

    def raises(
        self, expected_exception: _ExceptionTypes, *, update: bool = False
    ) -> "_RaisesContext":
        """Assert that a code block raises an expected exception
        and snapshot the value of the raised exception.

        This is directly inspired by the ``pytest.raises`` method.

        This method must be used as a context manager:
        ```python
        >>> snapshot: Snapshot
        >>> with snapshot.raises(ValueError):
        ...    raise ValueError("This message will be part of the snapshot. ")
        ```

        Args:
            expected_exception: BaseException type or tuple of BaseException types
              used to assert against the type of the raised exception.
            update: Whether to update the snapshot associated with the raised exception.

        Raises:
            TypeError: If the arguments to this method have invalid types.
        """
        # Type checking and type coercion of expected_exception argument.
        expected_exceptions: Tuple[type, ...]
        if isinstance(expected_exception, type):
            expected_exceptions = (expected_exception,)
        elif isinstance(expected_exception, tuple):
            expected_exceptions = expected_exception
        else:
            raise TypeError(
                "Expected exception must be a BaseException type or a tuple of "
                f"BaseException types. Found: {expected_exception}"
            )
        for exc in expected_exceptions:
            if not isinstance(exc, type) or not issubclass(exc, BaseException):
                name = exc.__name__ if isinstance(exc, type) else type(exc).__name__
                raise TypeError(
                    f"Expected exception must be a BaseException type, not {name}"
                )

        # Preload the metadata and snapshot file.
        self._metadata = self._get_metadata(update_on_next_run=update, args_to_ignore=[])
        self._snapshot_file = self._load_snapshot_file(metadata=self._metadata)
        return _RaisesContext(self, expected_exceptions, update)

    def __enter__(self) -> "Snapshot":
        """Enter the context of a Snapshot session."""
        self._within_context = True
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exits the context of the Snapshot session."""
        if self._snapshot_file is not None:
            self._snapshot_file.write()
        self._within_context = False

    @staticmethod
    def _construct_diff(value: Any, expected: Any, comparison: ObjectComparison) -> str:
        """Construct the human-readable diff between two objects.

        Args:
            value: The value to be diffed.
            expected: The object to be diffed against.
            comparison: The ObjectComparison object used to summarize the differences.

        Return:
            A multiline string with the following format:
              <git-style diff between value and expected>
              --------------------------------------------------------
              Summary:
                 <Bulleted list of summaries>
        """
        difference_summaries = comparison.differences.items.values()
        # 2 less than the terminal width because the Differ adds 2 characters to each line.
        width = get_terminal_size().columns - 2
        value_formatted = f"{pprint.pformat(value, width=width)}\n"
        expected_formatted = f"{pprint.pformat(expected, width=width)}\n"
        result = Differ().compare(
            value_formatted.splitlines(keepends=True),
            expected_formatted.splitlines(keepends=True),
        )

        return (
            "".join(result)
            + ("-" * width)
            + "\n"
            + "Summary:\n"
            + "\n".join(f"  > {difference}" for difference in difference_summaries)
            + "\n"
        )

    def _get_metadata(
        self, update_on_next_run: bool, args_to_ignore: List[str]
    ) -> SnapshotMetadata:
        """Gather metadata via inspection of current context of the test function.

        A SnapshotMetadata object is created only if self._metadata is not already set.
        However, the "update_on_next_run" attribute is set every time.

        Args:
            update_on_next_run: Setting for SnapshotMetadata.update_on_next_run
            args_to_ignore: Will specifically ignore certain inputs in the metadata
        """
        if isinstance(self._metadata, SnapshotMetadata):
            self._metadata.update_on_next_run = update_on_next_run
            return self._metadata

        # frame_index is set to 3 here to access the function scope of the test function
        #  test_function                                   <- frame_index=3
        #    | - Snapshot.assert_match                     <- frame_index=2
        #          | - Snapshot._get_metadata              <- frame_index=1
        #                | - CallerInfo.from_call_stack    <- frame_index=0
        caller_info = CallerInfo.from_call_stack(frame_index=3)
        caller_info = self._remove_special_arguments(caller_info)

        # Ignore certain arguments
        [caller_info.args.pop(item) for item in args_to_ignore]

        return SnapshotMetadata(
            caller_info=caller_info, update_on_next_run=update_on_next_run
        )

    def _load_snapshot_file(self, metadata: SnapshotMetadata) -> "_SnapshotFile":
        """Load the snapshot file into memory.

        The snapshot file is only loaded if self._snapshot_file is not already set.

        Args:
            metadata: The SnapshotMetadata object used to identify the correct snapshots.
        """
        if isinstance(self._snapshot_file, _SnapshotFile):
            return self._snapshot_file
        return _SnapshotFile(config=self.configuration, metadata=metadata)

    @classmethod
    def _remove_special_arguments(cls, caller_info: CallerInfo) -> CallerInfo:
        """Filter out the any arguments that shouldn't be used for metadata,
        such as the pytest "snapshot" fixture.

        Args:
            caller_info: The `snappiershot.inspection.CallerInfo` object to be filtered.

        Return:
            The filtered CallerInfo object.
        """
        arguments_to_remove = [
            key for key, value in caller_info.args.items() if isinstance(value, cls)
        ]
        for argument in arguments_to_remove:
            del caller_info.args[argument]
        return caller_info
