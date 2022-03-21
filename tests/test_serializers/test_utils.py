""" Tests for snappiershot/serializers/utils.py """
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from snappiershot.serializers.utils import (
    default_encode_value,
    encode_exception,
    fullvars,
    get_snapshot_file,
)


class TestDefaultEncodeValue:
    """ Tests for the default_encode_value utility function. """

    @staticmethod
    def test_encode_class():
        """ Test that a class is encoded as expected. """
        # Arrange
        value = SimpleNamespace(a=1, b="banana", c=None)
        expected = dict(a=1, b="banana", c=None)

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_class_recursive():
        """ Test that a class is recursively encoded as expected. """
        # Arrange
        value = SimpleNamespace(
            class_=SimpleNamespace(a=1, b="banana", c=None),
            dict_=dict(key_1="value_1", key_2="value_2"),
            list_=["item_1", "item_2"],
        )
        expected = dict(
            class_=dict(a=1, b="banana", c=None),
            dict_=dict(key_1="value_1", key_2="value_2"),
            list_=["item_1", "item_2"],
        )

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_custom_encoder():
        """ Test that a class that specifies a custom encoder
        gets encoded using that method.
        """
        # Arrange
        encoding = "CUSTOM ENCODING"

        class ClassWithCustomEncoder:
            """ Example class with custom encoder. """

            # noinspection PyMethodMayBeStatic
            def __snapshot__(self):
                """ Custom encoder for snappiershot. """
                return encoding

        value = ClassWithCustomEncoder()

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == encoding

    @staticmethod
    def test_encode_serializable_types():
        """ Test that a class with custom-encoded types does not encode these types. """
        # Arrange
        from datetime import datetime

        complex_value = 3 + 4j
        datetime_value = datetime(2020, 10, 8)
        value = SimpleNamespace(complex=complex_value, datetime=datetime_value)
        expected = dict(complex=complex_value, datetime=datetime_value)

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize("value", (set("abcdefg"), (1, 2, 3)))
    def test_encode_collection_types(value):
        """ Test that a class with custom-encoded types does not encode collection. """
        # Arrange

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == value

    @staticmethod
    @pytest.mark.parametrize("value", [isinstance, type, iter([1, 2])])
    def test_encode_unserializable(value):
        """ Test that an unserializable object raises an error. """
        # Arrange

        # Act & Assert
        with pytest.raises(ValueError):
            default_encode_value(value)

    @staticmethod
    def test_encode_unserializable_recurse():
        """ Test that a class with un-serializable attributes does not error. """
        # Arrange
        value = SimpleNamespace(
            class_=SimpleNamespace(good="class", bad=type),
            dict_=dict(good="dict", bad=dict),
            list_=["list", list],
        )
        expected = dict(class_=dict(good="class"), dict_=dict(good="dict"), list_=["list"])

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_recursive_object():
        """ Test that recursive objects are handled gracefully. """
        # Arrange
        value = SimpleNamespace(class_=None, dict_=None, list_=None)
        value.class_ = value
        value.dict_ = dict(normal="string", recursive=value)
        value.list_ = [value, 1]
        expected = dict(dict_=dict(normal="string"), list_=[1])

        # Act
        import warnings

        with warnings.catch_warnings(record=True) as record:
            result = default_encode_value(value)

        # Assert
        assert result == expected
        assert all("recursive" in warn.message.args[0] for warn in record)

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        [
            # fmt: off
            (pd.DataFrame({'a': [1, 2, 3], 'balloons': ['are', 'awesome', SimpleNamespace(floating='wicker', propelled_by='fire')]}),
             {'index': [0, 1, 2],
              'columns': ['a', 'balloons'],
              'data': [[1, 'are'], [2, 'awesome'], [3, dict(floating='wicker', propelled_by='fire')]]}),
            (pd.Series({0: 1, 1: 2, 2: SimpleNamespace(balloons="are awesome")}),
             {'index': [0, 1, 2],
              'data': [1, 2, dict(balloons="are awesome")]}),
            # fmt: on
        ],
    )
    def test_encode_pandas_recurse(value, expected) -> None:
        """
        Test recursive encoding of pandas objects
        """
        # Arrange

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        [
            # fmt: off
            (np.array(['balloons', 'are', 'awesome']), ['balloons', 'are', 'awesome']),
            ([np.float16(4), np.uint(4)], [4, 4]),
            # fmt: on
        ],
    )
    def test_encode_numpy_recurse(value, expected) -> None:
        """
        Test recursive encoding of numpy objects
        """
        # Arrange

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_slots_class():
        """ Test default encoding of recursive slots-optimized classes. """
        # Arrange
        class SlotsClass:
            __slots__ = ("a", "b", "c", "d")

            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = self

        value = SlotsClass()

        # Act
        result = default_encode_value(value)

        # Assert
        assert result == dict(a=1, b=2)

    @staticmethod
    def test_uninstantiated_class():
        """ Test encoding for uninstantiated classes with a special skip function defined """

        # Arrange
        class UninstantiatedClass:
            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = 3

            @classmethod
            def __snapshotskip__(cls):
                encoding = "Dont Encode Me!"
                return encoding

        # Act
        result = default_encode_value(UninstantiatedClass)

        # Assert
        assert result == "Dont Encode Me!"


class TestGetSnapshotFile:
    """ Tests for the get_snapshot_file utility function. """

    @staticmethod
    def test_get_snapshot_file(tmp_path):
        """ Test that get_snapshot_file returns the expected path. """
        # Arrange
        test_file = tmp_path / "example_test.py"
        suffix = ".json"
        expected = tmp_path / ".snapshots" / "example_test.json"

        # Act
        returned = get_snapshot_file(test_file, suffix)

        # Assert
        assert returned == expected
        assert returned.parent.exists()

    @staticmethod
    def test_get_snapshot_file_directory_error(tmp_path):
        """ Test that get_snapshot_file raises an error if the directory
        containing the test does not exist.
        """
        # Arrange
        test_file = tmp_path / "sub-directory" / "example_test.py"
        suffix = ".json"

        # Act & Assert
        with pytest.raises(NotADirectoryError):
            get_snapshot_file(test_file, suffix)

    @staticmethod
    def test_get_snapshot_file_type_error(tmp_path):
        """ Test that get_snapshot_file raises an error for an invalid suffix. """
        # Arrange
        test_file = tmp_path / "example_test.py"
        suffix = "json"

        # Act & Assert
        with pytest.raises(TypeError):
            get_snapshot_file(test_file, suffix)


class TestEncodingExceptions:
    """ Tests for exception encoding. """

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        # fmt: off
        [(ValueError("That's a bad value"),
          dict(exception_type="ValueError",
               exception_value="That's a bad value")),
         (OSError(2, "No such file or directory", "<><"),
          dict(exception_type="FileNotFoundError",
               exception_value="[Errno 2] No such file or directory: '<><'")),
         ]
        # fmt: on
    )
    def test_write_json_error(value, expected):
        """ Test if an error occurs during snapshot writing, no file is written. """
        # Arrange

        # Act
        result = encode_exception(value)

        # Assert
        assert result == expected


class TestFullVars:
    """ Tests for the fullvars. """

    @staticmethod
    def test_regular_class():
        """ Test that fullvars works for a regular class. """
        # Arrange
        class NormalClass:
            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = 3

        klass = NormalClass()

        # Act
        result = fullvars(klass)

        # Assert
        assert result == dict(a=1, b=2, c=3)

    @staticmethod
    def test_slots_class():
        """ Test that fullvars works for a slots-optimized class. """
        # Arrange
        class SlotsClass:
            __slots__ = ("a", "b", "c")

            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = 3

        klass = SlotsClass()

        # Act
        result = fullvars(klass)

        # Assert
        assert result == dict(a=1, b=2, c=3)

    @staticmethod
    def test_slots_class_partial_instantiated():
        """ Test that fullvars works for a slots-optimized class
        with partially instantiated slots. """
        # Arrange
        class SlotsClassPartiallyInstantiated:
            __slots__ = ("a", "b", "c")

            def __init__(self):
                self.a = 1
                self.b = 2

        klass = SlotsClassPartiallyInstantiated()

        # Act
        result = fullvars(klass)

        # Assert
        assert result == dict(a=1, b=2)

    @staticmethod
    def test_mixed_class():
        """ Test that fullvars works for classes with __slots__ and __dict__. """
        # Arrange
        class MixedClass:
            __slots__ = ("__dict__", "a", "b")

            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = 3

        klass = MixedClass()

        # Act
        result = fullvars(klass)

        # Assert
        assert result == dict(a=1, b=2, c=3)

    @staticmethod
    def test_empty_class():
        """ Test that fullvars works for an empty class. """
        # Arrange
        class EmptyClass:
            pass

        klass = EmptyClass()

        # Act
        result = fullvars(klass)

        # Assert
        assert result == dict()

    @staticmethod
    def test_to_dict_class():
        """ Test that fullvars works for classes with to_dict. """
        # Arrange
        class ToDictClass:
            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = 3

            def to_dict(self):
                return getattr(self, "__dict__", dict())

        klass = ToDictClass()

        # Act
        result = fullvars(klass)

        # Assert
        assert result == dict(a=1, b=2, c=3)
