""" Package level imports and versioning. """

# Python version compatibility.
try:
    # >= 3.8
    import importlib.metadata as metadata
except ImportError:
    #  < 3.8
    import importlib_metadata as metadata


__version__ = ""
try:
    __version__ = metadata.version(__name__)
except FileNotFoundError:
    pass
