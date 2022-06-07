# THIS IS A TEST

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
  * `__snapshot__` is a workaround described below


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
`__snapshot__` overrides serializing behavior for class objects being recorded. Some of its potential use cases:
  * Partially recording class objects with many unnecessary properties
  * Skipping over encoding an object by returning a string

```python
from snappiershot import Snapshot
from pytest import fixture

class TestClass1:
  def __init__(self):
    self.a = 1
    self.b = 2

  def __snapshot__(self) -> dict:
    encoding = {
      "a": self.a,
      "b": self.b,
    }
    return encoding

class TestClass2:
  def __init__(self):
    self.a = 1
    self.b = 2

  def __snapshot__(self) -> str:
    encoding = "ENCODING SKIPPED"
    return encoding

@fixture
def class_input1() -> TestClass1:
  class_input1 = TestClass1()
  return class_input1

@fixture
def class_input2() -> TestClass2:
  class_input2 = TestClass2()
  return class_input2

def test_class1(class_input1: TestClass1, snapshot: Snapshot):
    """ Test encoding snapshot and metadata for a custom class with a dictionary override"""

    # Act
    result = class_input1

    # Assert
    snapshot.assert_match(result)

def test_class2(class_input2: TestClass2, snapshot: Snapshot):
    """ Test encoding snapshot and metadata for a custom class with a string override """

    # Act
    result = class_input2

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
  * Classes with custom encoding (by defining a `__snapshot__` method)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)
