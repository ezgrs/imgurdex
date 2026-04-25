import abc

from imgurbc.domain.models.resource import Resource


class Downloader(abc.ABC):
    @abc.abstractmethod
    async def download(self, id: str) -> Resource | None: ...
