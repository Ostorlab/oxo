"""Abstract Asset class to define the scan target and its properties."""
import abc
from ostorlab import exceptions
from ostorlab.agent.message import serializer

class MissingTargetSelector(exceptions.OstorlabError):
    """Missing asset selector definition."""


class Asset(abc.ABC):
    """Abstract Asset class to define the scan target and its properties."""

    selector: str = None

    def to_proto(self) -> bytes:
        if self.selector is None:
            raise MissingTargetSelector()
        return serializer.serialize(self.selector, self.__dict__).SerializeToString()


def selector(target: str):
    """Decorator to define an asset selector for serialization.

    Args:
        target: Target selector.

    Returns:
        Selector initializer function.
    """

    def _selector_initializer(asset: Asset) -> Asset:
        """Set asset selector."""
        asset.selector = target
        return asset

    return _selector_initializer
