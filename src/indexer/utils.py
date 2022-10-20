from functools import wraps, lru_cache
from typing import Callable, Iterable

from cachetools import LRUCache, keys
from starknet_py.contract import Contract
from starknet_py.net.client_models import GatewayBlock
from starknet_py.net.gateway_client import GatewayClient
from cachetools import keys


# TODO: check https://docs.openzeppelin.com/contracts-cairo/0.3.1/utilities
def int_to_bytes(n: int) -> bytes:
    return n.to_bytes(32, "big")


def str_to_felt(text):
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")


def felt_to_str(felt: int) -> str:
    length = (felt.bit_length() + 7) // 8
    return felt.to_bytes(length, byteorder="big").decode("utf-8")


def async_cached(cache, key=keys.hashkey):
    """Returns decorator function to cache async function results.

    This is a replacement for `@cached()` decorator from cachetools.
    cachetools does not support async at the time of writing.

    Source: https://github.com/aiocoro/async-cached
    """

    def decorator(func):
        if cache is None:

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

        else:

            @wraps(func)
            async def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    pass
                v = await func(*args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass
                return v

        return wrapper

    return decorator


@async_cached(cache=LRUCache(maxsize=128))
async def get_contract(address, client: GatewayClient) -> Contract:
    return await Contract.from_address(address, client=client)


@async_cached(cache=LRUCache(maxsize=128))
async def get_block(block_number: int, client: GatewayClient) -> GatewayBlock:
    return await client.get_block(block_number=block_number)


@lru_cache(maxsize=128)
def get_contract_events(contract: Contract) -> dict:
    return {
        element["name"]: element
        for element in contract.data.abi
        if element["type"] == "event"
    }


def function_accepts(func: Callable, argnames: Iterable) -> bool:
    """Check if the given function has argnames as arguments

    Args:
        func (Callable): the function object
        argnames (Iterable): an iterable of argument names

    Example:
        >>> def foo(x, y, z):
        >>>     pass

        >>> function_accepts(foo, ['x', 'y'])
        >>> True

        >>> function_accepts(foo, ['x', 't'])
        >>> False

    Returns:
        bool: whether the function accepts the arguments or not
    """
    return all([argname in func.__code__.co_varnames for argname in argnames])