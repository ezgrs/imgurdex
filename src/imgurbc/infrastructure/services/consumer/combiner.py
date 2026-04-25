import typing


from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.models.resource import Resource


class CombinerConsumer(Consumer):
    _consumers: typing.Iterable[Consumer]

    def __init__(self, *, consumers: typing.Iterable[Consumer]) -> None:
        self._consumers = consumers

    async def consume_hit(self, resource: Resource) -> None:
        for consumer in self._consumers:
            await consumer.consume_hit(resource)

    async def consume_miss(self, id: str) -> None:
        for consumer in self._consumers:
            await consumer.consume_miss(id)
