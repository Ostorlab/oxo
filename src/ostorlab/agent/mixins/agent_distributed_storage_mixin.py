import redis

class AgentDistributedStorageMixin:

    def __init__(self, redis_url: str) -> None:
        self._redis_client = redis.Redis.fr

    def is_or_mark_as_tested(self, dna) -> bool:
        """Helper function that takes care of reporting if the specified DNA has been tested in the past, or mark it
        as tested.

        The method should be used to sync multiple agents that may encounter he same test case but need to test it
         only once.

        :param dna: The DNA to verify if tested.
        :return:
        """
        return not bool(self.redis_client.sadd(self._name_, dna))

    def is_tested(self, dna) -> bool:
        return self.redis_client.sismember(self._name_, dna)
