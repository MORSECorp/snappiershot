""" Functionality relating to configuration of the Snappiershot package. """
from pathlib import Path
from typing import Any, Dict, Optional, Union

import tomlkit
from tomlkit.exceptions import TOMLKitError

PathType = Union[Path, str]

DEFAULT_FILE_FORMAT = "JSON"
DEFAULT_ABS_TOL = 1e-6
DEFAULT_REL_TOL = 0.001
DEFAULT_FULL_DIFF = False
DEFAULT_JSON_INDENT = 4


class Config:
    """ The configuration object used throughout the package. """

    def __init__(
        self,
        file_format: str = DEFAULT_FILE_FORMAT,
        float_absolute_tolerance: float = DEFAULT_ABS_TOL,
        float_relative_tolerance: float = DEFAULT_REL_TOL,
        full_diff: bool = DEFAULT_FULL_DIFF,
        json_indentation: int = DEFAULT_JSON_INDENT,
        **_kwargs: Dict,
    ):
        """
        Args:
            file_format: The file format type to use, current options are {JSON}.
            float_absolute_tolerance: The absolute tolerance used to compare floats.
            float_relative_tolerance: The relative tolerance used to compare floats.
            full_diff: Whether to display the full diff of snapshots on failure.
            json_indentation: The number of spaces to use for JSON-indentation.

        The ``**_kwargs`` argument is used to silently accept and ignore any extraneous
          configuration key-value pairs that are parsed from the pyproject.toml file.
        """
        self.file_format = file_format
        self.abs_tol = float_absolute_tolerance
        self.rel_tol = float_relative_tolerance
        self.full_diff = full_diff
        self.json_indentation = json_indentation
        self._validate()

    @classmethod
    def from_pyproject(cls, file: Path) -> "Config":
        """ Create a Config object by parsing a pyproject.toml file.

        Args:
            file: The path to the pyproject.toml file, as a `pathlib.Path` object.
        """
        try:
            pyproject_toml = tomlkit.parse(file.read_text())
            tool_config = pyproject_toml.get("tool", dict()).get("snappiershot", dict())
        except (TOMLKitError, FileNotFoundError):
            tool_config = dict()
        return Config(**tool_config)

    def _validate(self) -> None:
        """ Validates the configuration.

        Raises:
            ValueError: If a configuration has an invalid value.
            TypeError: If a configuration has an invalid type.
        """
        # Validate file_format.
        if not isinstance(self.file_format, str):
            raise TypeError(
                f"Expected a string value for the file_format configuration; "
                f"Found: {self.file_format}"
            )
        self.file_format = str(self.file_format).upper()  # Convert from tomlkit type.
        if self.file_format != DEFAULT_FILE_FORMAT:
            raise ValueError(
                f"The only supported file_format is {DEFAULT_FILE_FORMAT}; "
                f"Found: {self.file_format}"
            )

        # Validate abs_tol.
        if not isinstance(self.abs_tol, float):
            raise TypeError(
                f"Expected a float value for the float_absolute_tolerance configuration; "
                f"Found: {self.abs_tol}"
            )
        self.abs_tol = float(self.abs_tol)  # Convert from tomlkit type.
        if self.abs_tol < 0:
            raise ValueError(
                f"The float_absolute_tolerance configuration must be positive; "
                f"Found: {self.abs_tol}"
            )

        # Validate rel_tol.
        if not isinstance(self.rel_tol, float):
            raise TypeError(
                f"Expected a float value for the float_relative_tolerance configuration; "
                f"Found: {self.rel_tol}"
            )
        self.rel_tol = float(self.rel_tol)  # Convert from tomlkit type.
        if self.rel_tol < 0:
            raise ValueError(
                f"The float_relative_tolerance configuration must be positive; "
                f"Found: {self.rel_tol}"
            )

        # Validate full_diff
        if not isinstance(self.full_diff, bool):
            raise TypeError(
                f"Expected an boolean value for the full_diff configuration; "
                f"Found: {self.full_diff}"
            )

        # Validate json_indentation.
        if not isinstance(self.json_indentation, int):
            raise TypeError(
                f"Expected an integer value for the json_indentation configuration; "
                f"Found: {self.json_indentation}"
            )
        if self.json_indentation < 0:
            raise ValueError(
                f"The json_indentation configuration must be positive; "
                f"Found: {self.json_indentation}"
            )

    def __eq__(self, other: Any) -> bool:
        """ Check equality. """
        return isinstance(other, type(self)) and (vars(self) == vars(other))

    def __repr__(self) -> str:
        """ Human-readable representation. """
        return (
            "Config("
            f"file_format={self.file_format}, "
            f"abs_tol={self.abs_tol}, "
            f"rel_tol={self.rel_tol}, "
            f"full_diff={self.full_diff}, "
            f"json_indentation={self.json_indentation})"
        )


def find_pyproject_toml(source: PathType) -> Optional[Path]:
    """ Travel up the tree of the provided source, looking for a pyproject.toml file.

    Args:
        source: A path to the source from which to start the search.

    Returns:
        Path to the pyproject.toml file, if found, else None.
    """
    source = Path(source)
    haystack = [source, *source.parents] if source.is_dir() else source.parents
    for directory in haystack:
        needle = directory / "pyproject.toml"
        if needle.exists():
            return needle
    else:
        return None
