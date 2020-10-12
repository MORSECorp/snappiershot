""" Tooling necessary to make snappiershot a pytest plugin. """
from pathlib import Path
from typing import Iterator

import pytest
import snappiershot
from _pytest.config import Config as PytestConfig
from _pytest.config.argparsing import Parser as PytestParser
from _pytest.fixtures import FixtureRequest

from .tracker import SnapshotTracker

PACKAGE_CONFIG_OPTION = "_snappiershot_default_config"
PACKAGE_TRACKER_OPTION = "_snappiershot_tracker"
PACKAGE_FULL_DIFF_OPTION = "snappiershot_full_diff"


def construct_snappiershot_config(pytest_config: PytestConfig) -> snappiershot.Config:
    """ Attempt to construct a snappiershot.Config object from the pytest Config object.

    Uses various path locations stored in the pytest Config object to locate the
      any pyproject.toml files with snappiershot configurations.

    Args:
        pytest_config: The pytest Config object.
    """
    sources = pytest_config.inifile, pytest_config.rootdir, pytest_config.invocation_dir
    for source in filter(None, sources):
        pyproject_toml = snappiershot.config.find_pyproject_toml(source)
        if pyproject_toml is not None:
            config = snappiershot.Config.from_pyproject(pyproject_toml)
            config.full_diff |= pytest_config.getoption(PACKAGE_FULL_DIFF_OPTION)
            return config
    return snappiershot.Config()


def pytest_addoption(parser: PytestParser) -> None:
    """ Add options to the pytest runner configurations. """
    group = parser.getgroup("snappiershot")
    group.addoption(
        "--snappiershot-full-diff",
        action="store_true",
        default=False,
        dest=PACKAGE_FULL_DIFF_OPTION,
        help="Display full snapshot diff on failure. ",
    )


def pytest_configure(config: PytestConfig) -> None:
    """ Snappiershot-specific configuration for the pytest runner. """
    # Construct a default snappiershot.Config object during pytest initialization.
    setattr(config.option, PACKAGE_CONFIG_OPTION, construct_snappiershot_config(config))

    # If the `pytest --help` command is run, args is None.
    if hasattr(config, "args"):
        # Construct a SnapshotTracker object that tracks the state of each snapshot.
        root_dir = Path(config.rootdir).resolve()
        test_paths = (Path(path).resolve().relative_to(root_dir) for path in config.args)
        setattr(config.option, PACKAGE_TRACKER_OPTION, SnapshotTracker(*test_paths))


# noinspection PyShadowingNames
@pytest.fixture(name="snapshot", scope="function")
def _snapshot(request: FixtureRequest) -> Iterator[snappiershot.Snapshot]:
    """ Pytest fixture with function-level scope that returns a
    snappiershot.Snapshot object.

    Examples:
        >>> # test_file.py
        >>> def test_function(snapshot):
        ...     snapshot.assert_match({"test": "value"})

    """
    config: snappiershot.Config = request.config.getoption(PACKAGE_CONFIG_OPTION)
    with snappiershot.Snapshot(config) as snapshot:
        yield snapshot

    if (snapshot._metadata is not None) and (snapshot._snapshot_file is not None):
        tracker: SnapshotTracker = request.config.getoption(PACKAGE_TRACKER_OPTION)
        tracker.set_status(
            statuses=snapshot._snapshot_file._snapshot_statuses,
            snapshot_file=snapshot._snapshot_file._snapshot_file,
            function_name=snapshot._metadata.caller_info.function,
            metadata=snapshot._metadata,
        )
    else:
        # TODO: Add warning.
        pass
