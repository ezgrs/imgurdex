import abc
import collections.abc


class IdIterator(collections.abc.Iterator[str]):
    @abc.abstractmethod
    async def close(self) -> None: ...
