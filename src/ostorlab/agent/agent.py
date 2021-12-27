import abc


class Agent(abc.ABC):

    @abc.abstractmethod
    def process(self, message) -> None:
        raise NotImplementedError('Missing process method implementation.')