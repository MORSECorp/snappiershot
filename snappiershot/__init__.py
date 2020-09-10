""" Package level imports and versioning. """

# Python version compatibility.
try:
    # >= 3.8
    import importlib.metadata as metadata
except ImportError:
    #  < 3.8
    import importlib_metadata as metadata  # type: ignore

from .config import Config
from .inspection import CallerInfo
from .snapshot import Snapshot, SnapshotMetadata

__version__ = ""
try:
    __version__ = metadata.version(__name__)  # type: ignore
except FileNotFoundError:
    pass
