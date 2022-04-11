""" Fixtures shared throughout all tests. """
import warnings
from typing import List

import pytest


@pytest.fixture(autouse=True)
def warning_catcher() -> List[warnings.WarningMessage]:
    """Auto-used fixture for catching warning produced by the SnappierShot library.

    Examples:
        ```python
        >>> from snappiershot.errors import SnappierShotWarning
        >>> def test_function(warning_catcher: List[warnings.WarningMessage]):
        >>>     ...  # Test library in way that raises a warning
        >>>     assert warning_catcher
        >>>     assert warning_catcher[0].category == SnappierShotWarning
        ```

    """
    with warnings.catch_warnings(record=True) as warning_catcher:
        yield warning_catcher
