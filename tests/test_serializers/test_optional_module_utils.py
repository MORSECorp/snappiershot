""" Tests for snappiershot/serializers/optional_module_utils.py """
import pandas as pd
import pytest
from pytest_mock import MockFixture
from snappiershot.serializers.optional_module_utils import (
    get_pandas,
    is_pandas_object,
)


class TestPandas:
    def test_get_pandas(self) -> None:
        """
        Test get_pandas when module is present
        """
        # Arrange

        # Act
        result = get_pandas()

        # Assert
        assert result is pd

    def test_get_pandas_missing(self, mocker: MockFixture) -> None:
        """
        Test get_pandas when module is missing
        """
        # Arrange
        mocker.patch.dict("sys.modules", {"pandas": None})

        # Act
        result = get_pandas()

        # Assert
        assert result is None

    def test_get_pandas_missing_error(self, mocker: MockFixture) -> None:
        """
        Test get_pandas when module is missing raises error
        """
        # Arrange
        mocker.patch.dict("sys.modules", {"pandas": None})

        # Act / assert
        with pytest.raises(ImportError, match="foo"):
            get_pandas(raise_error=True, custom_error_message="foo")

    @pytest.mark.parametrize(
        "value, expected", [(pd.Series([1, 2, 3]), True), ([1, 2, 3], False)]
    )
    def test_is_pandas_object(self, value, expected) -> None:
        """
        Test is_pandas_object
        """
        # Arrange

        # Act
        result = is_pandas_object(value)

        # Assert
        assert result == expected
