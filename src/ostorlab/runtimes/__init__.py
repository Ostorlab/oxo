"""Ostorlab runtime module.
Runtimes are in charge of running a scan as defines by a set of agents, agent group and a target asset."""

from .local.runtime import LocalRuntime
from .runtime import AgentRunDefinition, AgentGroupDefinition, Runtime, AgentDefinition
