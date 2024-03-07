"""mock agent implements the required methods to test the agent's behavior without using external components."""

import dataclasses

import pytest

from typing import List

from ostorlab.agent.message import message as msg


@dataclasses.dataclass
class RawMessage:
    """Raw message as key selector without transformation and message body."""

    key: str
    message: bytes


@dataclasses.dataclass
class AgentRunInstance:
    """An instance run to collect all aspects of an agent instance."""

    emitted_messages: List[msg.Message] = dataclasses.field(default_factory=lambda: [])
    control_messages: List[msg.Message] = dataclasses.field(default_factory=lambda: [])
    raw_messages: List[RawMessage] = dataclasses.field(default_factory=lambda: [])


@pytest.fixture(scope="function")
def agent_mock(mocker) -> List[object]:
    """Fixture patches all the Agent components and returns the list of messages emitted"""
    emitted_messages: List[msg.Message] = []
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

    def mq_send_message(key, message):
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
def agent_persist_mock(mocker):
    """This fixture patches the Agent persist component and returns the list storage state"""
    storage = {}

    def _set_is_member(key, value):
        """Check values are present in the storage dict."""
        return key in storage and value in storage[key]

    def _set_add(key, *value):
        """Add members to the storage dict and emulate return value."""
        if all(_set_is_member(key, v) for v in value):
            return False
        else:
            for v in value:
                storage.setdefault(key, set()).add(v)
            return True

    def _set_len(key):
        if key in storage:
            return len(storage[key])

    def _set_members(key):
        if key in storage:
            return storage[key]

    def _get(key):
        if key in storage:
            return storage[key]

    def _add(key, value):
        """Check values are present in the storage dict."""
        storage[key] = str(value).encode()

    def _hash_add(hash_name, mapping):
        mapping = {k: str(v).encode() for k, v in mapping.items()}
        storage.setdefault(hash_name, {}).update(mapping)

    def _hash_exists(hash_name, key):
        if isinstance(storage.get(hash_name), dict):
            return key in storage.get(hash_name)
        return False

    def _hash_get(hash_name, key):
        if isinstance(storage.get(hash_name), dict):
            return storage.get(hash_name).get(key, None)
        else:
            return None

    def _hash_get_all(hash_name):
        return storage.get(hash_name, {})

    def _delete(key):
        storage.pop(key)

    def _value_type(key):
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
def agent_run_mock(mocker) -> AgentRunInstance:
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

    def mq_send_message(key, message):
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
