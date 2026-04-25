import typing

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.models.resource import Resource


class OutputToStreamConsumer(Consumer):
    _stream: typing.TextIO
    _hit_count: int
    _miss_count: int

    def __init__(self, *, stream: typing.TextIO) -> None:
        self._stream = stream
        self._hit_count = 0
        self._miss_count = 0

    def _format_stats(self) -> str:
        return f"{self._hit_count:2d}h, {self._miss_count:4d}m, {self._hit_count/(self._hit_count+self._miss_count):.2%}"

    async def consume_hit(self, resource: Resource) -> None:
        self._hit_count += 1
        self._stream.write(f"[X] ({self._format_stats()}) {resource.name}\n")

    async def consume_miss(self, id: str) -> None:
        self._miss_count += 1
        self._stream.write(f"[ ] ({self._format_stats()}) {id}\n")
