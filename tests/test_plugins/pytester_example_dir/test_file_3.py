""" This is a test file used for testing the pytest plugin. """
from pint.unit import Unit


def test_complex_snapshot(snapshot):
    """ The snapshot for this function is expected to exist, but the assertion fails. """

    class HasUnitsClass:
        def __init__(self):
            tmp_dict = {"unit": Unit("m"), "value": -1000}
            tmp_list = [tmp_dict, tmp_dict]

            self.test1 = tmp_dict
            self.test2 = tmp_list

    klass = HasUnitsClass()

    snapshot.assert_match(klass)
