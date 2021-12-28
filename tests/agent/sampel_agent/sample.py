from ostorlab.agent import Agent, Message, ReportMixin


class SampleAgent(Agent, ReportMixin):

    def __init__(self, speed, performance):
        self._speed = speed

    def process(self, message: Message) -> None:
        print('hello agent')
        self.emit(
            'a.b.c',
            message
        )

        self.report_vulnerability(

        )


class Sample2Agent(Agent):
    def process(self, message: Message) -> None:
        print('hello')
