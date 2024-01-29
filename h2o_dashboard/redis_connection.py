import asyncio

import aioredis
from h2o_wave import Q, app  # noqa F401

from pyokx.redis_structured_reports import get_account_report, get_positions_report, get_tickers_report, get_orders_report, get_balances_and_positions_report
from redis_tools.utils import _deserialize_from_redis, connect_to_aioredis


async def start_redis():
    global async_redis

    if 'async_redis' in globals() and isinstance(async_redis, aioredis.Redis):
        return
    async_redis = await connect_to_aioredis()

    if not async_redis:
        raise Exception("Redis connection failed")

    import h2o_dashboard
    h2o_dashboard.async_redis = async_redis

    return async_redis




async def stop_redis():
    await async_redis.close()



