""" This is a test file used for testing the pytest plugin. """


def test_function_passed(snapshot):
    """ The snapshot for this function is expected to exist. """
    snapshot.assert_match(3 + 4j)


def test_function_new(snapshot):
    """ The snapshot for this function is expected to exist, but only one assertion is expected. """
    snapshot.assert_match(3 + 4j)
    snapshot.assert_match(3 + 4j)
