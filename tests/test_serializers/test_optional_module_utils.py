""" Tests for snappiershot/serializers/optional_module_utils.py """
import numpy as np
import pandas as pd
import pytest
from pytest_mock import MockFixture
from snappiershot.serializers.optional_module_utils import Numpy, Pandas


class TestPandas:
    @staticmethod
    def test_get_pandas() -> None:
        """
        Test get_pandas when module is present
        """
        # Arrange

        # Act
        result = Pandas.get_pandas()

        # Assert
        assert result is pd

    @staticmethod
    def test_get_pandas_missing(mocker: MockFixture) -> None:
        """
        Test get_pandas when module is missing
        """
        # Arrange
        mocker.patch.dict("sys.modules", {"pandas": None})

        # Act
        result = Pandas.get_pandas()

        # Assert
        assert result is None

    @staticmethod
    def test_get_pandas_missing_error(mocker: MockFixture) -> None:
        """
        Test get_pandas when module is missing raises error
        """
        # Arrange
        mocker.patch.dict("sys.modules", {"pandas": None})

        # Act / assert
        with pytest.raises(ImportError, match="foo"):
            Pandas.get_pandas(raise_error=True, custom_error_message="foo")

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected", [(pd.Series([1, 2, 3]), True), ([1, 2, 3], False)]
    )
    def test_is_pandas_object(value, expected) -> None:
        """
        Test is_pandas_object
        """
        # Arrange

        # Act
        result = Pandas.is_pandas_object(value)

        # Assert
        assert result == expected

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        [
            # fmt: off
            (pd.DataFrame({'a': [1, 2], 'balloons': ['are', 'awesome']}),
             {'index': [0, 1], 'columns': ['a', 'balloons'], 'data': [[1, 'are'], [2, 'awesome']]}),
            (pd.Series({0: 1, 1: 2}),
             {'index': [0, 1], 'data': [1, 2]}),
            # fmt: on
        ],
    )
    def test_encode_pandas(value, expected) -> None:
        """
        Test encode_pandas
        """
        # Arrange

        # Act
        result = Pandas.encode_pandas(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_encode_pandas_error():
        """ Test that the encode_pandas raises an error if no encoding is defined. """
        # Arrange
        value = "not a pandas"

        # Act & Assert
        with pytest.raises(NotImplementedError):
            Pandas.encode_pandas(value)


class TestNumpy:
    @staticmethod
    def test_get_numpy() -> None:
        """
        Test get_numpy when module is present
        """
        # Arrange

        # Act
        result = Numpy.get_numpy()

        # Assert
        assert result is np

    @staticmethod
    def test_get_numpy_missing(mocker: MockFixture) -> None:
        """
        Test get_numpy when module is missing
        """
        # Arrange
        mocker.patch.dict("sys.modules", {"numpy": None})

        # Act
        result = Numpy.get_numpy()

        # Assert
        assert result is None

    @staticmethod
    def test_get_numpy_missing_error(mocker: MockFixture) -> None:
        """
        Test get_numpy when module is missing raises error
        """
        # Arrange
        mocker.patch.dict("sys.modules", {"numpy": None})

        # Act / assert
        with pytest.raises(ImportError, match="foo"):
            Numpy.get_numpy(raise_error=True, custom_error_message="foo")

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected", [(np.array([1, 2, 3]), True), ([1, 2, 3], False)]
    )
    def test_is_numpy_object(value, expected) -> None:
        """
        Test is_numpy_object
        """
        # Arrange

        # Act
        result = Numpy.is_numpy_object(value)

        # Assert
        assert result == expected

    @staticmethod
    def test_get_numpy_primatives() -> None:
        """
        Test _get_numpy_primatives
        """
        # Arrange

        # Act
        result = Numpy._get_numpy_primatives(np)

        # Assert
        assert len(result) == 33  # Expected number of types
        for thing in result:
            assert "numpy" in getattr(thing, "__module__", "").split(
                "."
            )  # Check that type is from numpy
            assert type(thing) is type  # Check that each type is a type

    @staticmethod
    def test_encode_numpy_error():
        """ Test that the encode_numpy raises an error if no encoding is defined. """
        # Arrange
        value = "not a numpy"

        # Act & Assert
        with pytest.raises(NotImplementedError):
            Numpy.encode_numpy(value)

    @staticmethod
    @pytest.mark.parametrize(
        "value, expected",
        [
            # fmt: off
            (np.array([['balloons'], ['are'], ['awesome']]),
             [['balloons'], ['are'], ['awesome']]),
            (np.bool_(1), True),
            (np.byte(4), 4),
            (np.ubyte(4), 4),
            (np.short(4), 4),
            (np.ushort(4), 4),
            (np.intc(4), 4),
            (np.uintc(4), 4),
            (np.int_(4), 4),
            (np.uint(4), 4),
            (np.longlong(4), 4),
            (np.ulonglong(4), 4),
            (np.float16(4), 4),
            (np.single(4), 4),
            (np.double(4), 4),
            (np.longdouble(4), 4),
            (np.csingle(4), 4),
            (np.cdouble(4), 4),
            (np.clongdouble(4), 4),
            (np.int8(4), 4),
            (np.int16(4), 4),
            (np.int32(4), 4),
            (np.int64(4), 4),
            (np.uint8(4), 4),
            (np.uint16(4), 4),
            (np.uint32(4), 4),
            (np.uint64(4), 4),
            (np.intp(4), 4),
            (np.uintp(4), 4),
            (np.float32(4), 4),
            (np.float64(4), 4),
            (np.complex64(4), 4 + 0j),
            (np.complex128(4), 4 + 0j),
            (np.complex_(4), 4 + 0j),
            (np.random.default_rng(), "numpy.random._generator.Generator - encoding skipped")
            # fmt: on
        ],
    )
    def test_encode_numpy(value, expected) -> None:
        """
        Test encode_numpy
        """
        # Arrange

        # Act
        result = Numpy.encode_numpy(value)

        # Assert
        assert result == expected
