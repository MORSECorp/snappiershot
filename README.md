# SnappierShot
Add snapshot testing to your testing toolkit.

## Installation
```bash
$ pip install snappiershot
```

## Configuration
Snappier shot is following the [trend of packages](https://github.com/carlosperate/awesome-pyproject/)
in performing project-wide configuration through the pyproject.toml file established by
[PEP 518](https://www.python.org/dev/peps/pep-0518/).

Within the pyproject.toml file, all snappiershot configuration can be found under the
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

#### No Test Runner Example
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

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)
