""" Tests for snappiershot.snapshot._raises.py """

import pytest
from snappiershot.snapshot import Snapshot
from snappiershot.snapshot._raises import _RaisesContext


def test_no_exception_raised(snapshot: Snapshot):
    """ Test that the expected error is raised when no exception is caught. """
    # Arrange
    raises = _RaisesContext(snapshot, BaseException, False)

    # Act & Assert
    with pytest.raises(ValueError):
        with raises:
            pass


def test_wrong_exception_raised(snapshot: Snapshot):
    """ Test that the expected error is raised when no exception is caught. """
    # Arrange
    raises = _RaisesContext(snapshot, ValueError, False)

    # Act & Assert
    with pytest.raises(TypeError):
        with raises:
            raise FileNotFoundError
