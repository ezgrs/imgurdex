import aiopath

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.models.resource import Resource


class StoreAsLocalFileConsumer(Consumer):
    _base_dir: aiopath.AsyncPath

    def __init__(self, *, base_dir: aiopath.AsyncPath) -> None:
        self._base_dir = base_dir

    async def consume_hit(self, resource: Resource) -> None:
        await self._base_dir.mkdir(parents=True, exist_ok=True)
        await (self._base_dir / resource.name).write_bytes(resource.contents)

    async def consume_miss(self, id: str) -> None:
        return
