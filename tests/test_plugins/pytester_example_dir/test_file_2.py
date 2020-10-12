""" This is a test file used for testing the pytest plugin. """
import pytest


@pytest.mark.xfail
def test_function_fail(snapshot):
    """ The snapshot for this function is expected to exist, but the assertion fails. """
    snapshot.assert_match(False)


def test_function_write(snapshot):
    """ The snapshot for this function is not expected to exist. """
    snapshot.assert_match(3 + 4j)
