# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from typing import List

import aioredis

from pyokx.data_structures import FillHistoricalMetrics
from pyokx.ws_data_structures import AccountChannel, PositionsChannel, OrdersChannel, available_channel_models
from redis_tools.utils import _deserialize_from_redis

'''Structured Websocket Streams'''


async def get_stream_okx_all_messages(async_redis: aioredis.Redis, count: int = 10):
    messages_serialized = await async_redis.xrevrange('okx:websockets@all', count=count)
    if not messages_serialized:
        print(f"no messages in all cache!")
        return []

    messages_serialized.reverse()

    messages = []
    for message in messages_serialized:
        redis_stream_id = message[0]
        message_serialized = message[1].get("data")
        if not message_serialized:
            print(
                f"A message in the all stream {'okx:websockets@all'} with id {redis_stream_id} was empty, skipping")
            continue
        message_deserialized = _deserialize_from_redis(message_serialized)
        message_channel = message_deserialized.get("arg").get("channel")
        data_struct = available_channel_models[message_channel]
        if hasattr(data_struct, "from_array"):
            structured_message = data_struct.from_array(**message_deserialized)
        else:
            structured_message = data_struct(**message_deserialized)
        messages.append(structured_message)
    return messages


async def get_stream_okx_account_messages(async_redis: aioredis.Redis, count: int = 10) -> List[AccountChannel]:
    """Uses xrevrange to get the latest COUNT account messages from redis and return all COUNT messages
        in a list from oldest to newest"""
    account_messages_serialized = await async_redis.xrevrange('okx:websockets@account', count=count)
    if not account_messages_serialized:
        print(f"account information not ready in account cache!")
        return []

    account_messages_serialized.reverse()

    account_messages = []
    for account_message in account_messages_serialized:
        redis_stream_id = account_message[0]
        account_message_serialized = account_message[1].get("data")
        if not account_message_serialized:
            print(
                f"A message in the account stream {'okx:websockets@account'} with id {redis_stream_id} was empty, skipping")
            continue
        account_message_deserialized = _deserialize_from_redis(account_message_serialized)
        account_message: AccountChannel = AccountChannel(**account_message_deserialized)
        account_messages.append(account_message)
    return account_messages


async def get_stream_okx_position_messages(async_redis: aioredis.Redis, count: int = 10) -> List[PositionsChannel]:
    position_messages_serialized = await async_redis.xrevrange('okx:websockets@positions', count=count)
    if not position_messages_serialized:
        print(f"positions information not ready in position cache!")
        return []

    position_messages_serialized.reverse()

    position_messages = []
    for position_message in position_messages_serialized:
        redis_stream_id = position_message[0]
        position_message_serialized = position_message[1].get("data")
        if not position_message_serialized:
            print(
                f"A message in the positions stream {'okx:websockets@positions'} with id {redis_stream_id} was empty, skipping")
            continue
        position_message_deserialized = _deserialize_from_redis(position_message_serialized)
        position_message: PositionsChannel = PositionsChannel(**position_message_deserialized)
        position_messages.append(position_message)
    return position_messages


async def get_stream_okx_order_messages(async_redis: aioredis.Redis, count: int = 10):
    order_messages_serialized = await async_redis.xrevrange('okx:websockets@orders', count=count)
    if not order_messages_serialized:
        print(f"orders information not ready in order cache!")
        return []

    order_messages_serialized.reverse()

    order_messages = []
    for order_message in order_messages_serialized:
        redis_stream_id = order_message[0]
        order_message_serialized = order_message[1].get("data")
        if not order_message_serialized:
            print(
                f"A message in the orders stream {'okx:websockets@orders'} with id {redis_stream_id} was empty, skipping")
            continue
        order_message_deserialized = _deserialize_from_redis(order_message_serialized)
        order_message: OrdersChannel = OrdersChannel(**order_message_deserialized)
        order_messages.append(order_message)
    return order_messages


'''Structured Report Streams'''


async def get_stream_okx_fill_metrics_report(async_redis: aioredis.Redis, count: int = 10):
    fill_metrics_report_serialized = await async_redis.xrevrange('okx:reports@fill_metrics', count=count)
    if not fill_metrics_report_serialized:
        print(f"fills information not ready in fills cache!")
        return []

    fill_metrics_report_serialized.reverse()

    fill_metrics_report: List[FillHistoricalMetrics] = []
    for fill_metrics in fill_metrics_report_serialized:
        redis_stream_id = fill_metrics[0]
        fill_metrics_serialized = fill_metrics[1].get("data")
        if not fill_metrics_serialized:
            print(
                f"A message in the fills stream {'okx:reports@fill_metrics'} with id {redis_stream_id} was empty, skipping")
            continue
        fill_metrics_deserialized = _deserialize_from_redis(fill_metrics_serialized)
        fill_metrics = FillHistoricalMetrics(**fill_metrics_deserialized)
        fill_metrics_report.append(fill_metrics)
    return fill_metrics_report
