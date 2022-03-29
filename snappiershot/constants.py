""" Constants used throughout the snappiershot package. """
from types import SimpleNamespace

ENCODING_FUNCTION_NAME = "__snapshot__"
METADATA_ENCODING_OVERRIDE = "__metadata_override__"
SNAPSHOT_DIRECTORY = ".snapshots"


class SnapshotKeys(SimpleNamespace):
    """ Centralized location for the names of the keys of the parsed snapshot file. """

    metadata = "metadata"
    tests = "tests"
    snapshots = "snapshots"
    update = "update_on_next_run"
    version = "snappiershot_version"
