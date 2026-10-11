"""mock agent implements the required methods to test the agent's behavior without using external components."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from typing import Optional
from typing import cast

import pytest
from pytest_mock import plugin

from ostorlab.agent.message import message as msg


@dataclasses.dataclass
class RawMessage:
    """Raw message as key selector without transformation and message body."""

    key: str
    message: bytes


@dataclasses.dataclass
class AgentRunInstance:
    """An instance run to collect all aspects of an agent instance."""

    emitted_messages: list[msg.Message] = dataclasses.field(default_factory=list)
    control_messages: list[msg.Message] = dataclasses.field(default_factory=list)
    raw_messages: list[RawMessage] = dataclasses.field(default_factory=list)


StorageKey = str | bytes
StorageValue = bytes | set[str | bytes] | dict[str | bytes, bytes]
Storage = dict[StorageKey, StorageValue]


@pytest.fixture(scope="function")
def agent_mock(mocker: plugin.MockerFixture) -> Iterator[list[msg.Message]]:
    """Fixture patches all the Agent components and returns the list of messages emitted"""
    emitted_messages: list[msg.Message] = []
    mocker.patch(
        "ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_init", return_value=None
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_run", return_value=None
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.start_healthcheck",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.add_healthcheck",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.__init__",
        return_value=None,
    )

    def mq_send_message(
        key: str, message: bytes, message_priority: Optional[int] = None
    ) -> None:
        # we need to remove the last part of the key f'{selector}.{uuid.uuid1()}'
        control_message = msg.Message.from_raw("v3.control", message)
        agent_message = msg.Message.from_raw(
            ".".join(key.split(".")[:-1]), control_message.data["message"]
        )
        emitted_messages.append(agent_message)

    mocker.patch(
        "ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_send_message",
        side_effect=mq_send_message,
    )
    yield emitted_messages
    emitted_messages = []


@pytest.fixture(scope="function")
def agent_persist_mock(mocker: plugin.MockerFixture) -> Iterator[Storage]:
    """This fixture patches the Agent persist component and returns the list storage state"""
    storage: Storage = {}

    def _set_is_member(key: StorageKey, value: str | bytes) -> bool:
        """Check values are present in the storage dict."""
        return key in storage and value in cast(set[str | bytes], storage[key])

    def _set_add(key: StorageKey, *value: str | bytes) -> bool:
        """Add members to the storage dict and emulate return value."""
        if all(_set_is_member(key, v) for v in value):
            return False
        else:
            for v in value:
                cast(set[str | bytes], storage.setdefault(key, set())).add(v)
            return True

    def _set_len(key: StorageKey) -> Optional[int]:
        if key in storage:
            return len(storage[key])
        return None

    def _set_members(key: StorageKey) -> Optional[set[str | bytes]]:
        if key in storage:
            return cast(set[str | bytes], storage[key])
        return None

    def _get(key: StorageKey) -> Optional[StorageValue]:
        if key in storage:
            return storage[key]
        return None

    def _add(key: str | bytes, value: bytes) -> None:
        """Check values are present in the storage dict."""
        if isinstance(value, bytes) is False:
            value = str(value).encode()
        storage[key] = value

    def _exists(key: str | bytes) -> bool:
        """Check if thr key is present in the storage dict."""
        return key in storage

    def _hash_add(hash_name: StorageKey, mapping: dict[StorageKey, bytes]) -> None:
        for k, v in mapping.items():
            if isinstance(v, bytes) is False:
                mapping[k] = str(v).encode()
        cast(dict[StorageKey, bytes], storage.setdefault(hash_name, {})).update(mapping)

    def _hash_exists(hash_name: StorageKey, key: StorageKey) -> bool:
        if isinstance(storage.get(hash_name), dict):
            return key in cast(dict[StorageKey, bytes], storage.get(hash_name))
        return False

    def _hash_get(hash_name: StorageKey, key: StorageKey) -> Optional[bytes]:
        if isinstance(storage.get(hash_name), dict):
            return cast(dict[StorageKey, bytes], storage.get(hash_name)).get(key, None)
        else:
            return None

    def _hash_get_all(hash_name: StorageKey) -> StorageValue:
        return storage.get(hash_name, {})

    def _delete(key: StorageKey) -> None:
        storage.pop(key)

    def _value_type(key: StorageKey) -> str:
        if isinstance(storage.get(key), set):
            return "set"
        elif isinstance(storage.get(key), bytes):
            return "string"
        elif isinstance(storage.get(key), dict):
            return "hash"
        else:
            return "none"

    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.set_add",
        side_effect=_set_add,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.set_is_member",
        side_effect=_set_is_member,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.set_len",
        side_effect=_set_len,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.set_members",
        side_effect=_set_members,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.get",
        side_effect=_get,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.add",
        side_effect=_add,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.exists",
        side_effect=_exists,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.hash_add",
        side_effect=_hash_add,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.hash_exists",
        side_effect=_hash_exists,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.hash_get",
        side_effect=_hash_get,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.hash_get_all",
        side_effect=_hash_get_all,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.delete",
        side_effect=_delete,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.value_type",
        side_effect=_value_type,
    )

    yield storage
    storage = {}


@pytest.fixture(scope="function")
def agent_run_mock(mocker: plugin.MockerFixture) -> Iterator[AgentRunInstance]:
    """Improved fixture implementation to capture all aspects of an agent run in an `AgentRunInstance` object."""

    agent_run_instance = AgentRunInstance(raw_messages=[], emitted_messages=[])

    mocker.patch(
        "ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_init", return_value=None
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_run", return_value=None
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.start_healthcheck",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.add_healthcheck",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.__init__",
        return_value=None,
    )

    def mq_send_message(
        key: str, message: bytes, message_priority: Optional[int] = None
    ) -> None:
        # we need to remove the last part of the key f'{selector}.{uuid.uuid1()}'
        # Control Message.
        control_message = msg.Message.from_raw("v3.control", message)
        agent_run_instance.control_messages.append(control_message)
        # Raw Message.
        agent_run_instance.raw_messages.append(
            RawMessage(key=key, message=control_message.data["message"])
        )
        # Data Message.
        agent_message = msg.Message.from_raw(
            ".".join(key.split(".")[:-1]), control_message.data["message"]
        )
        agent_run_instance.emitted_messages.append(agent_message)

    mocker.patch(
        "ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_send_message",
        side_effect=mq_send_message,
    )
    yield agent_run_instance
    agent_run_instance = AgentRunInstance(raw_messages=[], emitted_messages=[])
