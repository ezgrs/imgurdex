import random
import string
import typing

from imgurbc.domain.interfaces.id_iterator import IdIterator


class MemoryIdIterator(IdIterator):
    _it: typing.Iterator[str]

    def __init__(self, *, iterator: typing.Iterator[str]) -> None:
        self._it = iterator

    def __next__(self) -> str:
        return next(self._it)

    async def close(self) -> None:
        return
