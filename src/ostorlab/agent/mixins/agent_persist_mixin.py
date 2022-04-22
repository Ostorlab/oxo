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
import redis

from ostorlab.runtimes import definitions as runtime_definitions


class AgentPersistMixin:
    """Agent mixin to persist data. The mixin enables distributed storage of a group of agent replicas or for a single
     agent that needs reliable storage."""

    def __init__(self, agent_settings: runtime_definitions.AgentSettings) -> None:
        """Initializes the mixin from the agent settings.

        Args:
            agent_settings: Agent runtime settings.
        """
        if agent_settings.redis_url is None:
            raise ValueError('agent settings is missing redis url')
        self._redis_client = redis.Redis.from_url(agent_settings.redis_url)

    def set_add(self, key, value) -> bool:
        """Helper function that takes care of reporting if the specified DNA has been tested in the past, or mark it
        as tested.
        The method can be used to sync multiple agents that may encounter the same test input but need to test it
        only once.
        Storage is shared between agents, ensure the keys used are unique.

        Args:
            key: Set key.
            value: List of values to add to set.

        Returns:
            True if it is a new member, False otherwise.
        """
        return bool(self._redis_client.sadd(key, value))

    def set_is_member(self, key, value) -> bool:
        """Indicates whether value is member of the set identified by key.

        Args:
            key: The set key.
            value: The value to check.

        Returns:
            True if it is a member, False otherwise.
        """
        return self._redis_client.sismember(key, value)

    def set_len(self, key) -> bool:
        """Helper function that returns the set cardinality (number of elements) of the set stored at key.
        The method can be used to sync multiple agents that may receive test inputs but need to test
        less than X test inputs.
        Storage is shared between agents, ensure the keys used are unique.

        Args:
            key: Set key.

        Returns:
            the cardinality (number of elements) of the set, or 0 if key does not exist.
        """
        return self._redis_client.scard(key)

    def set_members(self, key) -> bool:
        """Helper function that returns the value of key.

        Args:
            key: Set key.

        Returns:
             the value of key, or nil when key does not exist.
        """
        return self._redis_client.smembers(key)

    def add(self, key, value) -> bool:
        """Helper function that Set key to hold the string value.

        Args:
            key: key.
            value: String.

        Returns:
            String status of the set command.
        """
        return self._redis_client.set(key, value)

    def get(self, key) -> bool:
        """Get the value of key. If the key does not exist the special value nil is returned.

        Args:
            key: key.

        Returns:
            the value of key, or nil when key does not exist.
        """
        return self._redis_client.get(key)
