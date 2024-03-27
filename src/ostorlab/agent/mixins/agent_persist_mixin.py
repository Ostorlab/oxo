"""Mixin to enable distributed storage for a group of agent replicas or for a single agent that needs reliable storage.

A typical use-case is ensuring that a message value is processed only once in case multiple other agent are producing
duplicates or similar ones.

Typical usage:

```python
    status_agent = agent_persist_mixin.AgentPersistMixin(agent_settings)
    status_agent.set_add('crawler_agent_asset_dna', dna)
    is_new = not status_agent.set_is_member()
```
"""

import ipaddress
import logging
from typing import Dict, Set, Callable, Optional, Union

import redis

from ostorlab.runtimes import definitions as runtime_definitions

logger = logging.getLogger(__name__)


class AgentPersistMixin:
    """Agent mixin to persist data. The mixin enables distributed storage of a group of agent replicas or for a single
    agent that needs reliable storage."""

    def __init__(self, agent_settings: runtime_definitions.AgentSettings) -> None:
        """Initializes the mixin from the agent settings.

        Args:
            agent_settings: Agent runtime settings.
        """
        if agent_settings.redis_url is None:
            raise ValueError("agent settings is missing redis url")
        self._redis_client = redis.Redis.from_url(agent_settings.redis_url)

    def set_add(self, key: Union[bytes, str], *value: Union[bytes, str]) -> bool:
        """Helper function that takes care of reporting if the specified DNA has been tested in the past, or mark it
        as tested.
        The method can be used to sync multiple agents that may encounter the same test input but need to test it
        only once.
        Storage is shared between agents, ensure the keys used are unique.

        Args:
            key: Set key.
            value: values to add to set.

        Returns:
            True if it is a new member, False otherwise.
        """
        return bool(self._redis_client.sadd(key, *value))

    def set_is_member(self, key: Union[bytes, str], value: Union[bytes, str]) -> bool:
        """Indicates whether value is member of the set identified by key.

        Args:
            key: Set key.
            value: The value to check.

        Returns:
            True if it is a member, False otherwise.
        """
        return self._redis_client.sismember(key, value) == 1

    def set_len(self, key: Union[bytes, str]) -> int:
        """Helper function that returns the set cardinality (number of elements) of the set stored at key.
        The method can be used to sync multiple agents that may receive test inputs but need to test
        less than X test inputs.
        Storage is shared between agents, ensure the keys used are unique.

        Args:
            key: Set key.

        Returns:
            The cardinality (number of elements) of the set, or 0 if key does not exist.
        """
        return self._redis_client.scard(key)

    def set_members(self, key: Union[bytes, str]) -> Set[bytes]:
        """Helper function that returns all the members of the set value stored at key.

        Args:
            key: Set key.

        Returns:
             The value of key, or empty set when key does not exist.
        """
        return self._redis_client.smembers(key)

    def add(self, key: Union[bytes, str], value: bytes) -> Optional[bool]:
        """Helper function that Set key to hold the string value.

        Args:
            key: Key for string value.
            value: Bytes value.

        Returns:
            Status of the set command.
        """
        return self._redis_client.set(key, value)

    def get(self, key: Union[bytes, str]) -> Optional[bytes]:
        """Get the value of key. If the key does not exist None is returned.

        Args:
            key: Key for string value.

        Returns:
            Value of key, or None when key does not exist.
        """
        return self._redis_client.get(key)

    def hash_add(
        self,
        hash_name: Union[bytes, str],
        mapping: Dict[Union[bytes, str], Union[bytes, str]],
    ) -> bool:
        """Set mapping within hash hash_name. If hash_name does not exist a new hash is created.
        If key exists, value is overriden.

        Args:
            hash_name: Name of the hash.
            mapping: Dict of key/value pairs that will be hadded to hash_name

        Returns:
            True if the key does not exist, False otherwise
        """
        return bool(self._redis_client.hset(name=hash_name, mapping=mapping))

    def hash_exists(self, hash_name: Union[bytes, str], key: Union[bytes, str]) -> bool:
        """Returns a boolean indicating if key exists within hash hash_name.

        Args:
            hash_name: Name of the hash.
            key: Key in the hash.

        Returns:
            True if the key exists in the hash.
        """
        return self._redis_client.hexists(hash_name, key)

    def hash_get(
        self, hash_name: Union[bytes, str], key: Union[bytes, str]
    ) -> Optional[bytes]:
        """Return the value of key within the hash hash_name.

        Args:
            hash_name: Name of the hash.
            key: Key in the hash.

        Returns:
            Value of the key stored in hash_name, None if the key does not exist.
        """
        return self._redis_client.hget(hash_name, key)

    def hash_get_all(self, hash_name: Union[bytes, str]) -> Dict:
        """Returns a dict of the hash’s name/value pairs.

        Args:
            hash_name: Name of the hash.

        Returns:
            Dict of the hash’s name/value pairs.
        """
        return self._redis_client.hgetall(hash_name)

    def delete(self, key: Union[bytes, str]) -> bool:
        """Delete a specific key.

        Args:
            key: Key of any type.

        Returns:
            True if the key is delete, False otherwise.
        """
        return bool(self._redis_client.delete(key))

    def value_type(self, key: Union[bytes, str]) -> str:
        """Return a string representation of the type of the value stored at key.

        Args:
            key: Key in redis.

        Returns:
            String representation of the type of value stored at key. eg: set, string.
        """
        return self._redis_client.type(key).decode()

    def add_ip_network(
        self,
        key: Union[bytes, str],
        ip_range: Union[ipaddress.IPv6Network, ipaddress.IPv4Network],
        value: Optional[
            Callable[
                [Union[ipaddress.IPv6Network, ipaddress.IPv4Network]], Union[bytes, str]
            ]
        ] = None,
    ) -> bool:
        """
        Returns True if a network have never been persisted before, else it's returns False
        this method takes
        Args:
            key: Unique key for the set or a callable that gets the ip network getting check and returns the key.
            ip_range: IPv4Network or IPv4Network network to persist
            value: Callable to format the IP network. This is helpful to add extra data to the range, like for instance
             the port or service in case many needs to be tested separately.

        Returns:
            returns True if network is added and False if the network or one of it's super nets already exits.
        """
        ip_network = ip_range
        while ip_network.prefixlen != 0:
            if value is not None:
                member_value = value(ip_network)
            else:
                member_value = ip_network.exploded
            if self.set_is_member(key, member_value) is True:
                return False
            ip_network = ip_network.supernet()

        if value is not None:
            member_value = value(ip_range)
        else:
            member_value = ip_range.exploded
        return self.set_add(key, member_value)

    def ip_network_exists(
        self,
        key: Union[bytes, str],
        ip_range: Union[ipaddress.IPv6Network, ipaddress.IPv4Network],
        value: Optional[
            Callable[
                [Union[ipaddress.IPv6Network, ipaddress.IPv4Network]], Union[bytes, str]
            ]
        ] = None,
    ) -> bool:
        """
        Returns False if a network have never been persisted before, else it returns True.

        this method takes
        Args:
            key: key for the set
            ip_range: IPv4Network or IPv4Network network to check
            value: Callable to format the IP network. This is helpful to add extra data to the range, like for instance
             the port or service in case many needs to be tested separately.

        Returns:
            returns False if network is never been persisted (diff to add_ip_network shouldn't add it)
            and True if the network or one of it's super nets already exits.
        """
        ip_network = ip_range
        while ip_network.prefixlen != 0:
            if value is not None:
                member_value = value(ip_network)
            else:
                member_value = ip_network.exploded
            if self.set_is_member(key, member_value) is True:
                return True
            ip_network = ip_network.supernet()

        return False
