import asyncio

import aioredis
from h2o_wave import Q, app  # noqa F401

from pyokx.okx_market_maker.market_data_service.model.Tickers import Tickers
from pyokx.okx_market_maker.order_management_service.model.Order import Orders
from pyokx.okx_market_maker.position_management_service.model.Account import Account
from pyokx.okx_market_maker.position_management_service.model.BalanceAndPosition import BalanceAndPosition
from pyokx.okx_market_maker.position_management_service.model.Positions import Positions
from redis_tools.utils import connect_to_aioredis, _deserialize_from_redis


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


async def get_account() -> Account:
    account_report_serialized = await async_redis.xrevrange('okx:reports@account', count=1)
    if not account_report_serialized:
        print(f"account information not ready in account cache!")
        return Account()
    account_report_serialized = account_report_serialized[0][1]
    account_report_deserialized = _deserialize_from_redis(account_report_serialized)
    account: Account = Account().from_dict(account_dict=account_report_deserialized)
    return account


async def get_positions() -> Positions:
    positions_report_serialized = await async_redis.xrevrange('okx:reports@positions', count=1)
    if not positions_report_serialized:
        print(f"positions information not ready in positions cache!")
        return Positions()
    positions_report_serialized = positions_report_serialized[0][1]
    positions_report_deserialized = _deserialize_from_redis(positions_report_serialized)
    positions: Positions = Positions().from_dict(positions_dict=positions_report_deserialized)
    return positions


async def get_tickers() -> Tickers:
    tickers_report_serialized = await async_redis.xrevrange(f'okx:reports@tickers',
                                                            count=1)
    if not tickers_report_serialized:
        print(f"tickers information not ready in tickers cache!")
        return Tickers()
    tickers_report_serialized = tickers_report_serialized[0][1]
    tickers_report_deserialized = _deserialize_from_redis(tickers_report_serialized)
    tickers: Tickers = Tickers().from_dict(tickers_dict=tickers_report_deserialized)
    return tickers


async def get_orders() -> Orders:
    orders_report_serialized = await async_redis.xrevrange('okx:reports@orders', count=1)
    if not orders_report_serialized:
        print(f"orders information not ready in orders cache!")
        return Orders()
    orders_report_serialized = orders_report_serialized[0][1]
    orders_report_deserialized = _deserialize_from_redis(orders_report_serialized)
    orders: Orders = Orders().from_dict(orders_dict=orders_report_deserialized)
    return orders


async def get_balances_and_positions() -> BalanceAndPosition:
    # BalanceAndPosition
    balance_report_serialized = await async_redis.xrevrange('okx:reports@balance_and_position', count=1)
    if not balance_report_serialized:
        print(f"account information not ready in account cache!")
        return BalanceAndPosition()
    balance_report_serialized = balance_report_serialized[0][1]
    balance_report_deserialized = _deserialize_from_redis(balance_report_serialized)
    balance_and_position: BalanceAndPosition = BalanceAndPosition().from_dict(
        balance_and_position_dict=balance_report_deserialized)
    return balance_and_position


async def refresh_redis(q: Q):
    """
    Refreshes the Redis cache.

    :return: None
    """

    (q.user.okx_account, q.user.okx_positions,
     q.user.okx_tickers, q.user.okx_orders,q.user.okx_balances_and_positions) = await asyncio.gather(
        get_account(), get_positions(), get_tickers(), get_orders(), get_balances_and_positions())

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
