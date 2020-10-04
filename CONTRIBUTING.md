# CONTRIBUTING GUIDELINES

[Mozilla on OS Contributing Guidelines](https://mozillascience.github.io/working-open-workshop/contributing/)

Guidelines must include a requirement to fill out CLA before contributing.
This should be validated on PRs before accepting them.


## Running Tests
The easiest way to run tests is by running the `run_tests.sh` bash script
  from within the virtual environment in the root directory of the project.
```bash
(.venv) snappiershot$ ./run_tests.sh
```
The reason for this script is because the `pytest-cov` plugin for the `pytest`
  test runner does not play nicely with packages that are pytest plugins.
Therefore, the `coverage` package must be interfaced with separately.
