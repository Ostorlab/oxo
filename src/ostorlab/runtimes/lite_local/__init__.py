"""Ostorlab lite local runtime modules. this module takes care of launching a scan in the
local machine but with little setup, like no MQ service, no scan persistence and no defaults
agents are started."""
from .runtime import LiteLocalRuntime
