""" Tests for snappiershot/config.py """
from pathlib import Path
from typing import Dict, List, Type

import pytest
from snappiershot.config import (
    DEFAULT_ABS_TOL,
    DEFAULT_FILE_FORMAT,
    DEFAULT_JSON_INDENT,
    DEFAULT_REL_TOL,
    DEFAULT_SIG_FIG,
    Config,
    find_pyproject_toml,
)

DEFAULT_CONFIG_KWARGS = dict(
    file_format=DEFAULT_FILE_FORMAT,
    significant_figures=DEFAULT_SIG_FIG,
    float_absolute_tolerance=DEFAULT_ABS_TOL,
    float_relative_tolerace=DEFAULT_REL_TOL,
    json_indentation=DEFAULT_JSON_INDENT,
)


# ===== Fixtures ===========================================


@pytest.fixture(name="pyproject_directory")
def _pyproject_directory(tmp_path: Path) -> Path:
    """ Fixture which creates the following directory structure in a temporary directory:

    temp
      | - child
            | - pyproject.toml
            | - grandchild
                  | - great-grandchild

    Returns:
        The lowest directory within the created directory structure.
    """
    lowest_directory = tmp_path / "child" / "grandchild" / "great-grandchild"
    lowest_directory.mkdir(parents=True)
    (tmp_path / "child" / "pyproject.toml").touch()
    return lowest_directory


# ===== Tests ==============================================


@pytest.mark.parametrize("parent_index, expected", [(0, True), (1, True), (2, False)])
def test_find_pyproject_toml(parent_index: int, expected: bool, pyproject_directory: Path):
    """ Test that the `snappiershot.config.find_pyproject_toml` function properly
    traverses the provided path searching for the pyproject.toml file.
    """
    # Arrange
    source = pyproject_directory.parents[parent_index]

    # Act
    pyproject_toml = find_pyproject_toml(source)

    # Assert
    assert (pyproject_toml is not None) is expected


# fmt: off
@pytest.mark.parametrize(
    "contents, config_kwargs",
    [
        ([], DEFAULT_CONFIG_KWARGS),
        (["[tool.snappiershot]"], DEFAULT_CONFIG_KWARGS),
        (["[tool.snappiershot]", "bad line"], DEFAULT_CONFIG_KWARGS),
        (["[tool.snappiershot]", "ignored_config = true"], DEFAULT_CONFIG_KWARGS),
        (["[tool.snappiershot]", "significant_figures = 2"], {**DEFAULT_CONFIG_KWARGS, "significant_figures": 2}),
        (["[tool.snappiershot]", "float_absolute_tolerance = 1E-4"], {**DEFAULT_CONFIG_KWARGS, "float_absolute_tolerance": 1e-4}),
        (["[tool.snappiershot]", "float_relative_tolerance = 0.1"], {**DEFAULT_CONFIG_KWARGS, "float_relative_tolerance": 0.1}),
        (["[tool.snappiershot]", "json_indentation = 3"], {**DEFAULT_CONFIG_KWARGS, "json_indentation": 3}),
    ]
)
# fmt: on
def test_from_pyproject(contents: List[str], config_kwargs: Dict, pyproject_directory: Path):
    """ Test that pyproject.toml files are parsed for configurations in a robust manner. """
    # Arrange
    pyproject_toml = find_pyproject_toml(pyproject_directory)
    pyproject_toml.open("w").writelines((f"{line}\n" for line in contents))
    expected = Config(**config_kwargs)

    # Act
    result = Config.from_pyproject(pyproject_toml)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "config_kwargs, expected_error",
    [
        ({**DEFAULT_CONFIG_KWARGS, "file_format": None}, TypeError),
        ({**DEFAULT_CONFIG_KWARGS, "file_format": "csv"}, ValueError),
        ({**DEFAULT_CONFIG_KWARGS, "significant_figures": 3.14}, TypeError),
        ({**DEFAULT_CONFIG_KWARGS, "significant_figures": -1}, ValueError),
        ({**DEFAULT_CONFIG_KWARGS, "float_absolute_tolerance": 2}, TypeError),
        ({**DEFAULT_CONFIG_KWARGS, "float_absolute_tolerance": -1e6}, ValueError),
        ({**DEFAULT_CONFIG_KWARGS, "float_relative_tolerance": 2}, TypeError),
        ({**DEFAULT_CONFIG_KWARGS, "float_relative_tolerance": -1e6}, ValueError),
        ({**DEFAULT_CONFIG_KWARGS, "json_indentation": -1}, ValueError),
        ({**DEFAULT_CONFIG_KWARGS, "json_indentation": 1.5}, TypeError),
    ]
)
def test_config_validate(config_kwargs: Dict, expected_error: Type[Exception]):
    """ Checks that validation of the configuration values occurs as expected. """
    # Arrange

    # Act & Assert
    with pytest.raises(expected_error):
        Config(**config_kwargs)
