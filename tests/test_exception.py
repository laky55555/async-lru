import asyncio
import gc
from typing import Callable

import pytest

from async_lru import alru_cache


async def test_alru_exception(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> None:
        1 / 0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, return_exceptions=True)

    check_lru(coro, hits=2, misses=1, cache=1, tasks=0)

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=2, misses=2, cache=1, tasks=0)


async def test_alru_exception_reference_cleanup(check_lru: Callable[..., None]) -> None:
    class CustomClass: ...

    @alru_cache()
    async def coro(val: int) -> None:
        leaky = CustomClass()
        1 / 0

    coros = [coro(v) for v in range(1000)]

    await asyncio.gather(*coros, return_exceptions=True)

    check_lru(coro, hits=0, misses=1000, cache=128, tasks=0)

    await asyncio.sleep(0.00001)
    gc.collect()

    assert (
        len([obj for obj in gc.get_objects() if isinstance(obj, CustomClass)]) == 128
    ), "Only objects in the cache should be left in memory."
