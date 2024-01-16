import asyncio
import json
import os

import aioredis
from h2o_wave import Q, app  # noqa F401


async def start_redis():
    global async_redis
    if 'async_redis' in globals() and isinstance(async_redis, aioredis.Redis):
        return
    try:
        host = 'localhost'
        async_redis = aioredis.from_url(f"redis://{host}:6379", decode_responses=True)
        await async_redis.ping()

    except Exception as e:
        print(f"Redis Error: {e}")
        try:
            host = os.getenv('REDIS_HOST', "redis")
            async_redis = aioredis.from_url(f"redis://{host}:6379", decode_responses=True)
            await async_redis.ping()
        except Exception as e:
            print(f"Redis Error: {e}")
            async_redis = None
            exit()


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

    (positions) = await asyncio.gather(
        # get_index_values('ws_baldata_element__index'),
        get_index_values('ws_posdata_element__index'),
        # get_index_values('ws_trades_element__index'),
    )
    q.user.okx_positions: positions = positions[0]

    # Get last from streams/okx_account in redis
    account = await async_redis.xrevrange('okx_account', count=1)
    decoded_account_data = json.loads(account[0][1]["data"])
    from pyokx.data_structures import AccountBalanceData
    q.user.okx_balances = [AccountBalanceData(**account_data) for account_data in decoded_account_data]


async def load_page_recipe_with_refresh(q: Q, page_callback_function):
    """
    Loads a page after updating the application models.

    :param q: Wave server Q object.
    :param page_callback_function: Callback function for page loading.
    :return: Result of the `page_callback_function` and `update_models` functions.

    """
    await page_callback_function(q)
    await q.page.save()
    return await asyncio.gather(page_callback_function(q), refresh_redis(q))

# listen to websocket
