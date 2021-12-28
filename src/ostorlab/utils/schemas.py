"""Constants of the paths for the Agent & Agent Group specifications."""
import pathlib

OSTORLAB_ROOT_PATH = pathlib.Path().resolve().parent
AGENT_SPEC_PATH = OSTORLAB_ROOT_PATH / "agent/schema/agent_schema.json"
AGENT_GROUP_SPEC_PATH = OSTORLAB_ROOT_PATH / "agent/schema/agentGroup_schema.json"
