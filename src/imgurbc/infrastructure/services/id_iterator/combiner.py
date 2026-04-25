import typing

from imgurbc.domain.interfaces.id_iterator import IdIterator


class CombinerIdIterator(IdIterator):
    _iterators: typing.Iterator[IdIterator]
    _current_iterator: IdIterator | None
    _close_callbacks: list[typing.Callable[[], typing.Awaitable[None]]]

    @classmethod
    def from_iterable(
        cls, iterators: typing.Iterable[IdIterator]
    ) -> "CombinerIdIterator":
        return cls(iterators=iter(iterators))

    def __init__(self, *, iterators: typing.Iterator[IdIterator]) -> None:
        self._iterators = iterators
        self._current_iterator = None
        self._close_callbacks = []

    def __next__(self) -> str:
        while True:
            current_iterator = self._current_iterator
            if current_iterator is not None:
                try:
                    return next(current_iterator)
                except StopIteration:
                    pass

            iterator = next(self._iterators)
            self._current_iterator = iterator
            self._close_callbacks.append(iterator.close)

    async def close(self) -> None:
        for callback in self._close_callbacks:
            await callback()
