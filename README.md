# SnappierShot
Add snapshot testing to your testing toolkit.

## Installation
```bash
$ pip install snappiershot
```

## Configuration
SnappierShot is following the [trend of packages](https://github.com/carlosperate/awesome-pyproject/)
in performing project-wide configuration through the `pyproject.toml` file established by
[PEP 518](https://www.python.org/dev/peps/pep-0518/).

Within the `pyproject.toml` file, all SnappierShot configuration can be found under the
`[tool.snappiershot]` heading. While the `[tool.snappiershot]` heading is optional, the
`[tool.poetry.plugins.pytest11]` heading must also be included.

### Example (with default values):
```toml
[tool.poetry.plugins.pytest11]
snappiershot = "snappiershot.plugins.pytest"

[tool.snappiershot]
file_format = "json"
float_absolute_tolerance = 1e-6
float_relative_tolerance = 0.001
full_diff = false
json_indentation = 4
```

Currently, the only allowed file format is JSON.

## Usage

SnappierShot allows you to take a "snapshot" of data the first time that a test
  is run, and stores it nearby in a `.snapshots` directory as a JSON. Then, for all
  subsequent times that test is run, the data is asserted to "match" the original
  data.

SnappierShot uses metadata to find tests stored in each snapshot file. Metadata is
  defined as the inputs to a test method.
* If the metadata is not found, a new file is Written.
* If the metadata is found, the contents of the snapshot are checked and can either Pass or Fail.
* If a snapshot file is found but the test isn't run, then the test is marked as Unchecked

### Best Practices
* Do not run `assert_match` within a loop
* Do not try to snapshot uninstantiated classes/objects or use them as inputs to a test method
* If an unsupported object type cannot be recorded, see [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on how
  to contribute to the project
  * `__snapshot__` and `__metadata_override__` are temporary workarounds described below


### Pytest Examples
```python
from snappiershot import Snapshot

def test_basic(snapshot: Snapshot):
    """ Will do a basic snapshotting of one value with no metadata """
    # Arrange
    x = 1
    y = 2

    # Act
    result = x + y

    # Assert
    snapshot.assert_match(result)

def test_ignore_metadata(snapshot: Snapshot, input_to_ignore: str = "ignore me"):
    """ Test that metadata gets ignored """
    # Arrange
    x = 1
    y = 2
    ignored_input = ["input_to_ignore"]

    # Act
    result = x + y

    # Assert
    snapshot.assert_match(result, ignore=ignored_input)
```

### No Test Runner Example
```python
from snappiershot import Snapshot

def test_no_pytest_runner():
    """ Run test without pytest runner """
    # Arrange
    x = 1
    y = 2

    # Act
    result = x + y

    # Assert
    with Snapshot() as snapshot:
        snapshot.assert_match(result)
```

### Custom Encoding and Override Examples
Warning: Use these methods is hacky and should not be relied on.


* `__snapshot__` overrides serializing behavior for objects being recorded
  * Useful for partially recording class objects with many unnecessary properties
* `__metadata_override__` overrides serializing behavior for metadata being recorded
  * Useful for recording type objects (uninstantiated classes) via bypassing the default
    encoding process

```python
from snappiershot import Snapshot as Snappy
from pytest import fixture

class CustomClass:
  def __init__(self):
    self.a = 1
    self.b = 2

  def __snapshot__(self):
    encoding = {
      "a": self.a,
      "b": self.b,
    }
    return encoding

  @classmethod
  def __metadata_override__(cls):
    return "test string"


@fixture
def instanced_input() -> CustomClass:
  instanced_input = CustomClass()
  return instanced_input

@fixture
def uninstanced_input() -> type(CustomClass):
  instanced_input = CustomClass
  return instanced_input

def test_class(uninstanced_input: type(CustomClass), instanced_input: CustomClass, snapshot: Snappy):
    """ Test encoding snapshot and metadata for a custom class both instanced and un-instanced """

    # Act
    result = (instanced_input, uninstanced_input)

    # Assert
    snapshot.assert_match(result)
```


### Raises
Snappiershot also allows you to record errors that are raised during
  the execution of a code block. This allows you to track how and when errors
  are reported more easily.

```python
def fallible_function():
    """ A function with an error state. """
    raise RuntimeError("An error occurred!")


def test_fallible_function(snapshot):
    """ Test that errors are being reported as expected"""
    # Arrange

    # Act & Assert
    with snapshot.raises(RuntimeError):
        fallible_function()
```

### Support Types:
  * Primitives (`bool`, `int`, `float`, `None`, `str`)
  * Numerics (`complex`)
  * Collections (`lists`, `tuples`, `sets`)
  * Dictionaries
  * Classes (with an underlying `__dict__`, `__slots__`, or `to_dict`)
  * Unit types from the `pint` package
  * Classes with custom encoding (by defining a `__snapshot__` or `__metadata_override__` method)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)
