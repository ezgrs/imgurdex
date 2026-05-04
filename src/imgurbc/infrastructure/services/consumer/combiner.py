import logging
import typing


from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.models.resource import Resource


class CombinerConsumer(Consumer):
    _consumers: typing.Iterable[Consumer]
    _logger: logging.Logger

    def __init__(
        self, *, consumers: typing.Iterable[Consumer], logger: logging.Logger
    ) -> None:
        self._consumers = consumers
        self._logger = logger

    async def consume_hit(self, resource: Resource) -> None:
        for consumer in self._consumers:
            try:
                await consumer.consume_hit(resource)
            except Exception:
                self._logger.error(
                    f"Error while consuming hit for resource {resource.id} in consumer {type(consumer)}",
                    exc_info=True,
                )

    async def consume_miss(self, id: str) -> None:
        for consumer in self._consumers:
            try:
                await consumer.consume_miss(id)
            except Exception:
                self._logger.error(
                    f"Error while consuming miss for id {id} in consumer {type(consumer)}",
                    exc_info=True,
                )
