"""Ostorlab runtime module.
Runtimes are in charge of running a scan as defines by a set of agents, agent group and a target asset."""

from ostorlab.runtimes.local.runtime import LocalRuntime
from ostorlab.runtimes.runtime import Runtime
from ostorlab.runtimes.definitions import AgentRunDefinition, AgentGroupDefinition, AgentDefinition
