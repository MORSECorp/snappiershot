""" Tests for snappiershot/encoders.py """
import numpy as np
import pytest
from snappiershot.encoders import _is_numpy_array, encode_value


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        (None, None),
        (12, 12),
        (3.14, 3.14),
        ("string", "string"),
        ([True, None, 7, "string"], [True, None, 7, "string"]),
        ((True, None, 7, "string"), [True, None, 7, "string"]),
        (np.array(1), 1),
        (np.array([1, 2, 3]), [1, 2, 3]),
        (np.array([[1, 2], [3, 4]]), [[1, 2], [3, 4]]),
    ],
)
def test_encode_value(value, expected):
    """ Test that the encode_value function encodes python objects as expected. """
    # Arrange

    # Act
    result = encode_value(value)

    # Assert
    assert result == expected


def test_encode_value_error():
    """ Test than a value with no encoder raises an error. """
    # Arrange
    value = 3 + 4j

    # Act & Assert
    with pytest.raises(NotImplementedError):
        encode_value(value)


@pytest.mark.parametrize(
    "value, expected",
    [(np.array([]), True), (np.array(1), True), (list(), False), (None, False)],
)
def test_is_numpy_array(value, expected):
    """ Test that the _is_numpy_array function correctly identifies np.ndarray objects. """
    # Arrange

    # Act
    result = _is_numpy_array(value)

    # Assert
    assert result == expected
