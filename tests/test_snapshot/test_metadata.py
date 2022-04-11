""" Tests for snappiershot/snapshot/metadata.py """
from pathlib import Path
from typing import Dict, Type

import pytest
from numpy import array
from snappiershot.inspection import CallerInfo
from snappiershot.snapshot.metadata import SnapshotMetadata


class TestSnapshotMetadata:
    """Tests for the snappiershot.snapshot.SnapshotMetadata object."""

    # Define a complicated class
    class ToDictClass:
        def __init__(self):
            self.foo = 1
            self.bar = 2

        def to_dict(self):
            return getattr(self, "__dict__", dict())

        def from_dict(self, *args):
            return self

    FAKE_CALLER_INFO = CallerInfo(
        file=Path("fake/file/path"),
        function="fake_fully_qualified_function_name",
        args={
            "foo": 1,
            "bar": "two",
            "foobar": [1, 2],
            "barfoo": array([1, 2]),
            "foofoo": {"foo": 1, "bar": 2},
            "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, 2)],
        },
    )

    FAKE_CALLER_INFO_CLASS = CallerInfo(
        file=Path("fake/file/path"),
        function="fake_fully_qualified_function_name",
        args={"foobar": ToDictClass()},
    )

    DEFAULT_METADATA_KWARGS = dict(
        caller_info=FAKE_CALLER_INFO,
        update_on_next_run=False,
        test_runner_provided_name="",
        user_provided_name="",
    )

    DEFAULT_METADATA_KWARGS_CLASS = dict(
        caller_info=FAKE_CALLER_INFO_CLASS,
        update_on_next_run=False,
        test_runner_provided_name="",
        user_provided_name="",
    )

    @staticmethod
    @pytest.mark.parametrize(
        "metadata_kwargs, expected_error",
        [
            ({**DEFAULT_METADATA_KWARGS, "caller_info": None}, TypeError),
            ({**DEFAULT_METADATA_KWARGS, "update_on_next_run": "foo"}, TypeError),
            ({**DEFAULT_METADATA_KWARGS, "test_runner_provided_name": 1.23}, TypeError),
            ({**DEFAULT_METADATA_KWARGS, "user_provided_name": 1.23}, TypeError),
        ],
    )
    def test_metadata_validate(metadata_kwargs: Dict, expected_error: Type[Exception]):
        """Checks that validation of the metadata values occurs as expected."""
        # Arrange

        # Act & Assert
        with pytest.raises(expected_error):
            SnapshotMetadata(**metadata_kwargs)

    @staticmethod
    @pytest.mark.parametrize(
        "metadata_kwargs, metadata_dict, matches",
        [
            (DEFAULT_METADATA_KWARGS, {"arguments": FAKE_CALLER_INFO.args}, True),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": 2,
                        "foobar": [1, 2],
                        "barfoo": [1, 2],
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, 2)],
                    }
                },
                False,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": [1, 2],
                        "barfoo": [1, 2],
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, 2)],
                    }
                },
                True,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": array([1, 2]),
                        "barfoo": array([1, 2]),
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, 2)],
                    }
                },
                True,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": [1, "two"],
                        "barfoo": [1, 2],
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, 2)],
                    }
                },
                False,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": array([1, 2]),
                        "barfoo": array([1, 2]),
                        "foofoo": {"foo": 1, "foobar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, 2)],
                    }
                },
                False,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": array([1, 2]),
                        "barfoo": array([1, 2]),
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "foobar": 2}, {1, 2}, (1, 2)],
                    }
                },
                False,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": array([1, 2]),
                        "barfoo": array([1, 2]),
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, "2"}, (1, 2)],
                    }
                },
                False,
            ),
            (
                DEFAULT_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": "two",
                        "foobar": array([1, 2]),
                        "barfoo": array([1, 2]),
                        "foofoo": {"foo": 1, "bar": 2},
                        "barbar": [{"foo": 1, "bar": 2}, {1, 2}, (1, "2")],
                    }
                },
                False,
            ),
            (
                DEFAULT_METADATA_KWARGS_CLASS,
                {"arguments": {"foobar": {"foo": 1, "bar": 2}}},
                True,
            ),
        ],
    )
    def test_metadata_matches(metadata_kwargs: Dict, metadata_dict: Dict, matches: bool):
        """Checks that the SnapshotMetadata.matches method functions as expected."""
        # Arrange
        metadata = SnapshotMetadata(**metadata_kwargs)

        # Act
        result = metadata.matches(metadata_dict)

        # Assert
        assert result == matches
