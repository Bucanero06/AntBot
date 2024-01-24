import asyncio

import aioredis
from h2o_wave import Q, app  # noqa F401

from pyokx.redis_handling import get_account, get_positions, get_tickers, get_orders, get_balances_and_positions
from redis_tools.utils import _deserialize_from_redis, connect_to_aioredis


async def start_redis():
    global async_redis
    if 'async_redis' in globals() and isinstance(async_redis, aioredis.Redis):
        return
    async_redis = await connect_to_aioredis()


async def stop_redis():
    await async_redis.close()


async def get_index_values(index_name):
    indexes_values = await async_redis.zrange(name=index_name, start=0, end=-1)
    values = [await async_redis.hgetall(index_name) for index_name in indexes_values]

    return values



async def refresh_redis(q: Q):
    """
    Refreshes the Redis cache.

    :return: None
    """

    (q.user.okx_account, q.user.okx_positions,
     q.user.okx_tickers, q.user.okx_orders, q.user.okx_balances_and_positions) = await asyncio.gather(
        get_account(async_redis), get_positions(async_redis), get_tickers(async_redis), get_orders(async_redis),
        get_balances_and_positions(async_redis))

    btc_usdt_index_ticker = await async_redis.xrevrange('okx:reports@index-tickers@BTC-USDT', count=1)
    if not btc_usdt_index_ticker:
        print(f"BTC-USDT index ticker not ready in index-tickers cache!")
    btc_usdt_index_ticker = _deserialize_from_redis(btc_usdt_index_ticker[0][1])
    from pyokx.ws_data_structures import IndexTickersChannel
    q.user.okx_index_ticker = IndexTickersChannel(**btc_usdt_index_ticker)


async def load_page_recipe_with_refresh(q: Q, page_callback_function):
    """
    Loads a page after updating the application models.

    :param q: Wave server Q object.
    :param page_callback_function: Callback function for page loading.
    :return: Result of the `page_callback_function` and `update_models` functions.

    """

    return await asyncio.gather(page_callback_function(q), refresh_redis(q))

# listen to websocket
