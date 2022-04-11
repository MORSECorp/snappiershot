""" Enumeration of statuses for individual snapshots. """
from enum import IntEnum, auto


class SnapshotStatus(IntEnum):
    """Enumeration of snapshot statuses.

    Unchecked -- The snapshot was discovered, but has not been asserted against.
    Failed    -- The snapshot assertion failed.
    Passed    -- The snapshot assertion passed.
    Recorded  -- The snapshot is staged to be written, but not yet written.
    Written   -- The snapshot was written (or overwritten).
    """

    UNCHECKED = auto()
    FAILED = auto()
    PASSED = auto()
    RECORDED = auto()
    WRITTEN = auto()
