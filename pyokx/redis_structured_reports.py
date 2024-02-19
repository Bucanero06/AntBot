
from typing import List

import aioredis

from pyokx.okx_market_maker.market_data_service.model.Tickers import Tickers
from pyokx.okx_market_maker.order_management_service.model.Order import Orders
from pyokx.okx_market_maker.position_management_service.model.Account import Account
from pyokx.okx_market_maker.position_management_service.model.BalanceAndPosition import BalanceAndPosition
from pyokx.okx_market_maker.position_management_service.model.Positions import Positions
from redis_tools.utils import _deserialize_from_redis



'''Reports Stream'''
async def get_stream_account_report(async_redis: aioredis.Redis, count=1) -> List[Account]:
    account_report_serialized = await async_redis.xrevrange('okx:reports@account', count=count)
    if not account_report_serialized:
        print(f"account information not ready in account cache!")
        return [Account()]

    account_report_serialized.reverse()

    accounts = []
    for account_report in account_report_serialized:
        account_report_serialized = account_report[1]
        account_report_deserialized = _deserialize_from_redis(account_report_serialized)
        account: Account = Account().from_dict(account_dict=account_report_deserialized)
        accounts.append(account)
    return accounts


async def get_stream_positions_report(async_redis: aioredis.Redis, count=1) -> List[Positions]:
    positions_reports_serialized = await async_redis.xrevrange('okx:reports@positions', count=count)
    if not positions_reports_serialized:
        print(f"positions information not ready in positions cache!")
        return [Positions()]

    positions_reports_serialized.reverse()

    positions = []
    for positions_report in positions_reports_serialized:
        positions_report_serialized = positions_report[1]
        positions_report_deserialized = _deserialize_from_redis(positions_report_serialized)
        positions_report: Positions = Positions().from_dict(positions_dict=positions_report_deserialized)
        positions.append(positions_report)
    return positions



'''Single Reports DEPRECATED, use Stream Reports instead'''
async def get_account_report(async_redis: aioredis.Redis) -> Account:
    account_report_serialized = await async_redis.xrevrange('okx:reports@account', count=1)
    if not account_report_serialized:
        print(f"account information not ready in account cache!")
        return Account()
    account_report_serialized = account_report_serialized[0][1]
    account_report_deserialized = _deserialize_from_redis(account_report_serialized)
    account: Account = Account().from_dict(account_dict=account_report_deserialized)
    return account

async def get_positions_report(async_redis: aioredis.Redis) -> Positions:
    positions_report_serialized = await async_redis.xrevrange('okx:reports@positions', count=1)
    if not positions_report_serialized:
        print(f"positions information not ready in positions cache!")
        return Positions()
    positions_report_serialized = positions_report_serialized[0][1]
    positions_report_deserialized = _deserialize_from_redis(positions_report_serialized)
    positions: Positions = Positions().from_dict(positions_dict=positions_report_deserialized)
    return positions


async def get_tickers_report(async_redis: aioredis.Redis) -> Tickers:
    tickers_report_serialized = await async_redis.xrevrange(f'okx:reports@tickers',
                                                            count=1)
    if not tickers_report_serialized:
        print(f"tickers information not ready in tickers cache!")
        return Tickers()
    tickers_report_serialized = tickers_report_serialized[0][1]
    tickers_report_deserialized = _deserialize_from_redis(tickers_report_serialized)
    tickers: Tickers = Tickers().from_dict(tickers_dict=tickers_report_deserialized)
    return tickers


async def get_orders_report(async_redis: aioredis.Redis) -> Orders:
    orders_report_serialized = await async_redis.xrevrange('okx:reports@orders', count=1)
    if not orders_report_serialized:
        print(f"orders information not ready in orders cache!")
        return Orders()
    orders_report_serialized = orders_report_serialized[0][1]
    orders_report_deserialized = _deserialize_from_redis(orders_report_serialized)
    orders: Orders = Orders().from_dict(orders_dict=orders_report_deserialized)
    return orders


async def get_balances_and_positions_report(async_redis: aioredis.Redis) -> BalanceAndPosition:
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
