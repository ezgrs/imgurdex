import abc

from imgurbc.domain.models.resource import Resource


class Consumer(abc.ABC):
    @abc.abstractmethod
    async def consume_miss(self, id: str) -> None: ...

    @abc.abstractmethod
    async def consume_hit(self, resource: Resource) -> None: ...
