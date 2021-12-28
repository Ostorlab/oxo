import datetime

from ostorlab.agent import agent
from ostorlab.runtimes import runtime


class StartTestAgent(agent.Agent):
    def start(self) -> None:
        self.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})


definition = runtime.AgentDefinition(
    name='start_test_agent',
    out_selectors=['v3.healthcheck.ping'])
settings = runtime.AgentInstanceSettings(
    bus_url='amqp://guest:guest@localhost:5672/',
    bus_exchange_topic='ostorlab_test',
    healthcheck_port=5301)

start_agent = StartTestAgent(definition, settings)
start_agent.run()
