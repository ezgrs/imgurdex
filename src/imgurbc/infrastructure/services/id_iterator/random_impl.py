import random
import string

from imgurbc.domain.interfaces.id_iterator import IdIterator


class RandomIdIterator(IdIterator):
    rng: random.Random

    @classmethod
    def no_seed(cls) -> "RandomIdIterator":
        return cls(rng=random.Random())

    def __init__(self, *, rng: random.Random) -> None:
        self.rng = rng

    def __next__(self) -> str:
        return "".join(
            self.rng.choices(string.ascii_letters + string.digits, k=7)
        )

    async def close(self) -> None:
        return
