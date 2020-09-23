""" Tests for snappiershot/compare.py """
from math import nan

import pytest
from snappiershot.compare import ObjectComparison
from snappiershot.config import Config

# ===== Fixtures ===========================================

ABS_TOL = 1e-6
REL_TOL = 0.001


@pytest.fixture(name="config", scope="module")
def _config() -> Config:
    """ Fixture that returns a static Config object. """
    return Config(float_absolute_tolerance=ABS_TOL, float_relative_tolerance=REL_TOL)


# ===== Unit Tests =========================================


@pytest.mark.parametrize(
    "value, expected, is_equal",
    [
        (dict(a=1, b=2), dict(a=1, b=2), True),
        (dict(a=1, c=3), dict(a=1, b=2), False),
        (dict(a=1, b=3), dict(a=1, b=2), False),
    ],
)
def test_compare_dictionaries(value, expected, config, is_equal):
    """ Test that dictionaries are compared as expected. """
    # Arrange

    # Act
    comparison = ObjectComparison(value, expected, config)

    # Assert
    assert comparison.equal == is_equal


@pytest.mark.parametrize(
    "value, expected, is_equal",
    [
        ([1, 2, 3], [1, 2, 3], True),
        ([1, 2, 3], [1, 2, 3, 4], False),
        ([1, 2, 4], [1, 2, 3], False),
    ],
)
def test_compare_sequences(value, expected, config, is_equal):
    """ Test that sequences are compared as expected. """
    # Arrange

    # Act
    comparison = ObjectComparison(value, expected, config)

    # Assert
    assert comparison.equal == is_equal


@pytest.mark.parametrize(
    "value, expected, is_equal",
    [
        ({1, 2, 3}, {1, 2, 3}, True),
        ({2, 3, 1}, {1, 2, 3}, True),
        ({1, 2, 3}, {1, 2, 3, 4}, False),
        ({1, 2, 4}, {1, 2, 3}, False),
    ],
)
def test_compare_sets(value, expected, config, is_equal):
    """ Test that sets are compared as expected. """
    # Arrange

    # Act
    comparison = ObjectComparison(value, expected, config)

    # Assert
    assert comparison.equal == is_equal


@pytest.mark.parametrize(
    "value, expected, exact, is_equal",
    [
        (1.0, 1.0, False, True),
        (1e-8 * (1 + REL_TOL), 1e-8, False, True),
        (1.0 + ABS_TOL, 1.0, False, True),
        (1e-8 + (2 * ABS_TOL), 1e-8, False, False),
        (1.0 + ABS_TOL, 1.0, True, False),
        (nan, nan, False, True),
        (nan, nan, True, False),
    ],
)
def test_compare_floats(value, expected, config, exact, is_equal):
    """ Test that floats are compared as expected. """
    # Arrange

    # Act
    comparison = ObjectComparison(value, expected, config, exact)

    # Assert
    assert comparison.equal == is_equal


def test_compare_types(config):
    """ Test that objects of different types are caught. """
    # Arrange
    value = None
    expected = 3.14

    # Act
    comparison = ObjectComparison(value, expected, config)

    # Assert
    assert not comparison.equal


# ===== Integration Tests ==================================


def test_compare(config):
    """ Test comparison of complex object with itself (Integration test). """
    # Arrange
    value = {
        "string": "TEST",
        "none": None,
        "integer": 12,
        "float": 3.14,
        "list": list(range(5)),
        "tuple": (True, False, None),
        "set": set("abcdefg"),
    }
    value["dict"] = value.copy()

    # Act
    comparison = ObjectComparison(value, value, config)

    # Assert
    assert comparison.equal
