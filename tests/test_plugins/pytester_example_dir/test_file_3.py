""" This is a test file used for testing the pytest plugin. """
from pint.unit import Unit


def test_units_snapshot(snapshot):
    """The snapshot for this function is expected to pass."""

    class HasUnits:
        def __init__(self):
            tmp_dict = {"unit": Unit("m"), "value": -1000}
            tmp_list = [tmp_dict, tmp_dict]

            self.test1 = tmp_dict
            self.test2 = tmp_list

    obj = HasUnits()

    snapshot.assert_match(obj)
