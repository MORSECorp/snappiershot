# SnappierShot
Add snapshot testing to your testing toolkit.

## Installation
```bash
$ pip install snappiershot
```

## Configuration
SnappierShot is following the [trend of packages](https://github.com/carlosperate/awesome-pyproject/)
in performing project-wide configuration through the pyproject.toml file established by
[PEP 518](https://www.python.org/dev/peps/pep-0518/).

Within the pyproject.toml file, all SnappierShot configuration can be found under the
`[tool.snappiershot]` heading.

### Example (with default values):
```toml
[tool.snappiershot]
file_format = "json"
float_absolute_tolerance = 1e-6
float_relative_tolerance = 0.001
full_diff = false
json_indentation = 4
```


## Usage

SnappierShot allows you to take a "snapshot" of data the first time that a test
  is run, and stores it nearby in a `.snapshots` directory. Then, for all
  subsequent times that test is run, the data is assert to "match" the original
  data.

### Pytest Example
```python
def test_something(snapshot):
    """ Test that something works as expected"""
    # Arrange
    x = 1
    y = 2

    # Act
    result = x + y

    # Assert
    snapshot.assert_match(result)
```

### No Test Runner Example
```python
from snappiershot import Snapshot

def test_something():
    """ Test that something works as expected"""
    # Arrange
    x = 1
    y = 2

    # Act
    result = x + y

    # Assert
    with Snapshot() as snapshot
        snapshot.assert_match(result)

test_something()
```

### Raises
Snappiershot also allows you to take a "snapshot" errors that are raised during
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
  * Classes (with an underlying `__dict__`)
  * Classes with custom encoding (by defining a `__snapshot__` method).

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)
Discord Server: https://discord.gg/Are4Ab8Hzd
