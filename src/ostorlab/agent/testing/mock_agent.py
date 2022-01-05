"""mock agent implements the required methods to test the agent's behaviors without using external components."""
import dataclasses
from abc import ABC

from typing import Any, List, Dict

from ostorlab.agent import agent


@dataclasses.dataclass
class MessageSelector:
    """Dataclass to define messages based on their selector."""
    message: Any
    selector: str


class MockAgent(agent.Agent, ABC):
    """MockAgent class implements the Agent class without the need to external components
    It can be used by the agents to test their behaviors
    """

    def __init__(self, *args, **kwargs):
        """Inits the Mockagent configuration.

                Args:
                    agent_definition: Agent definition dictating the settings of the agent, like name, in_selectors ...
                    agent_instance_definition: The running instance definition dictating custom settings
                     of the agent like bus
                     URL.
                """
        self.emit_message_with_selector_queue: List[MessageSelector] = []
        super().__init__(*args, **kwargs)

    def emit(self, selector: str, data: Dict[str, Any]) -> None:
        """Add the messages to a list"""

        self.emit_message_with_selector_queue.append(MessageSelector(message=data, selector=selector))

    async def mq_init(self):
        """No need to initialize the MQ channel pools or the executors to process the messages."""
        pass

    async def mq_run(self, delete_queue_first: bool = False):
        """We will not use the MQ for the tests """
        pass

    async def mq_close(self):
        """Nothing to do here since the channel was not initialized """
        pass

    def _is_mq_healthy(self) -> bool:
        """Agent health check method, to ensure MQ connection is working."""
        return True


def start_agent(agent_class: Any, *args, **kwargs):
    # Hot patching parent class
    agent_class.__bases__ = (MockAgent,)
    instance = agent_class(*args, **kwargs)
    return instance

