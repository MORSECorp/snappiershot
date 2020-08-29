"""
Snapshot encoders for snapshot de/serialization
"""
import abc
import json
from typing import Any

from .config import Config


@abc.ABC
class SnapshotEncoder:
    """Abstract base class for snapshot encoders"""

    @abc.abstractmethod
    def serialize(self, value: Any) -> str:
        """Serialize given value to string for snapshotting

        Args:
            value: value to be serialized

        Returns:
            string containing serialized value
        """

    @abc.abstractmethod
    def deserialize(self, value: str) -> Any:
        """Deserialize given snapshot string to python object

        Args:
            value: value to be serialized

        Returns:
            string containing serialized value
        """


class JsonSnapshotEncoder(SnapshotEncoder):
    """Encoder for de/serialization to/from JSON-formatted strings"""

    def __init__(self, configuration: Config):
        """

        Args:
            configuration: snapiershot configuration
        """
        self.configuration = configuration

    def serialize(self, value: Any) -> str:
        """Serialize given value to a JSON-formatted string for snapshotting

        Args:
            value: value to be serialized

        Returns:
            string containing serialized value
        """
        return json.dumps(value, default=str, indent=self.configuration.json_indentation)

    def deserialize(self, string: str) -> Any:
        """Deserialize given JSON string to a python object

        Args:
            string: JSON-formatted string to deserialize

        Returns:
            deserialized value
        """
        return json.loads(string)




