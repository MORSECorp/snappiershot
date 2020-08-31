"""
Custom snappiershot exceptions
"""


class SnappiershotError(Exception):
    """Snappiershot error"""


class SnapshotNotFoundError(SnappiershotError):
    """Snapshot not found error"""