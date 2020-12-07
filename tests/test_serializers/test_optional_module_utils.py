""" Tests for snappiershot/serializers/optional_module_utils.py """
import pandas as pd
import pytest
from pytest_mock import MockFixture
from snappiershot.serializers.optional_module_utils import Pandas


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
