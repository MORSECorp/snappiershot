""" Tests for snappiershot/snapshot/metadata.py """
from pathlib import Path
from typing import Dict, Type

import pytest
from numpy import array
from pint.unit import Unit
from snappiershot.inspection import CallerInfo
from snappiershot.snapshot.metadata import SnapshotMetadata


class TestSnapshotMetadata:
    """ Tests for the snappiershot.snapshot.SnapshotMetadata object. """

    # Define a complicated class
    class ComplicatedClass:
        def __init__(self):
            tmp_dict = {"unit": Unit("m"), "value": -1000}
            tmp_list = [tmp_dict, tmp_dict]

            self.test1 = tmp_dict
            self.test2 = tmp_list

        def to_dict(self):
            return getattr(self, "__dict__", dict())

        @classmethod
        def from_dict(cls, *args):
            return cls

    # Define a complicated class
    class SkippableClass:
        def __init__(self):
            self.test1 = 1
            self.test2 = 2

        @classmethod
        def __snapshotskip__(cls):
            return "Skip Me"

    FAKE_CALLER_INFO = CallerInfo(
        file=Path("fake/file/path"),
        function="fake_fully_qualified_function_name",
        args={"foo": 1, "bar": "two"},
    )

    COMPLICATED_CALLER_INFO = CallerInfo(
        file=Path("fake/file/path"),
        function="fake_fully_qualified_function_name",
        args={
            "foo": ComplicatedClass,
            "bar": [ComplicatedClass, ComplicatedClass],
            "foobar": [array([1, 2]), array([1, 2])],
            "barfoo": SkippableClass,
        },
    )

    DEFAULT_METADATA_KWARGS = dict(
        caller_info=FAKE_CALLER_INFO,
        update_on_next_run=False,
        test_runner_provided_name="",
        user_provided_name="",
    )

    COMPLICATED_METADATA_KWARGS = dict(
        caller_info=COMPLICATED_CALLER_INFO,
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
        """ Checks that validation of the metadata values occurs as expected. """
        # Arrange

        # Act & Assert
        with pytest.raises(expected_error):
            SnapshotMetadata(**metadata_kwargs)

    @staticmethod
    @pytest.mark.parametrize(
        "metadata_kwargs, metadata_dict, matches",
        [
            (DEFAULT_METADATA_KWARGS, {"arguments": FAKE_CALLER_INFO.args}, True),
            (DEFAULT_METADATA_KWARGS, {"arguments": {"foo": 1, "bar": 2}}, False),
            (
                COMPLICATED_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": [1, 2],
                        "foobar": [[1, 2], [1, 2]],
                        "barfoo": "Skip Me",
                    }
                },
                True,
            ),
            (
                COMPLICATED_METADATA_KWARGS,
                {
                    "arguments": {
                        "foo": 1,
                        "bar": [1, None],
                        "foobar": [1, 2],
                        "barfoo": "Skip Me",
                    }
                },
                False,
            ),
        ],
    )
    def test_metadata_matches(metadata_kwargs: Dict, metadata_dict: Dict, matches: bool):
        """ Checks that the SnapshotMetadata.matches method functions as expected. """
        # Arrange
        metadata = SnapshotMetadata(**metadata_kwargs)

        # Act
        result = metadata.matches(metadata_dict)

        # Assert
        assert result == matches
