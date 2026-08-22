"""Abstract Asset class to define the scan target and its properties."""

import abc
from collections.abc import Callable
from typing import Any

from ostorlab import exceptions
from ostorlab.agent.message import serializer


class MissingTargetSelector(exceptions.OstorlabError):
    """Missing asset selector definition."""


class Asset(abc.ABC):
    """Abstract Asset class to define the scan target and its properties."""

    selector: str

    def to_proto(self) -> Any:
        if self.selector is None:
            raise MissingTargetSelector()
        return serializer.serialize(self.selector, self.__dict__).SerializeToString()

    @property
    def proto_field(self) -> str:
        return "asset"


def selector(target: str) -> Callable[[type[Asset]], type[Asset]]:
    """Decorator to define an asset selector for serialization.

    Args:
        target: Target selector.

    Returns:
        Selector initializer function.
    """

    def _selector_initializer(asset: type[Asset]) -> type[Asset]:
        """Set asset selector."""
        asset.selector = target
        return asset

    return _selector_initializer
