from typing import List

import aioredis

from pyokx.websocket_handling import available_channel_models
from pyokx.ws_data_structures import AccountChannel, PositionsChannel, OrdersChannel
from redis_tools.utils import _deserialize_from_redis

'''Structured Messages Stream'''


async def get_stream_all_messages(async_redis: aioredis.Redis, count: int = 10):
    messages_serialized = await async_redis.xrevrange('okx:messages@all', count=count)
    if not messages_serialized:
        print(f"no messages in all cache!")
        return []

    messages_serialized.reverse()

    messages = []
    for message in messages_serialized:
        redis_stream_id = message[0]
        message_serialized = message[1]
        message_deserialized = _deserialize_from_redis(message_serialized)
        message_channel = message_deserialized.get("arg").get("channel")
        data_struct = available_channel_models[message_channel]
        if hasattr(data_struct, "from_array"):
            structured_message = data_struct.from_array(**message_deserialized)
        else:
            structured_message = data_struct(**message_deserialized)
        messages.append(structured_message)
    return messages


async def get_stream_account_messages(async_redis: aioredis.Redis, count: int = 10) -> List[AccountChannel]:
    """Uses xrevrange to get the latest COUNT account messages from redis and return all COUNT messages
        in a list from oldest to newest"""
    account_messages_serialized = await async_redis.xrevrange('okx:messages@account', count=count)
    if not account_messages_serialized:
        print(f"account information not ready in account cache!")
        return []

    account_messages_serialized.reverse()

    account_messages = []
    for account_message in account_messages_serialized:
        redis_stream_id = account_message[0]
        account_message_serialized = account_message[1]
        account_message_deserialized = _deserialize_from_redis(account_message_serialized)
        account_message: AccountChannel = AccountChannel(**account_message_deserialized)
        account_messages.append(account_message)
    return account_messages


async def get_stream_position_messages(async_redis: aioredis.Redis, count: int = 10) -> List[PositionsChannel]:
    position_messages_serialized = await async_redis.xrevrange('okx:messages@positions', count=count)
    if not position_messages_serialized:
        print(f"positions information not ready in position cache!")
        return []

    position_messages_serialized.reverse()

    position_messages = []
    for position_message in position_messages_serialized:
        redis_stream_id = position_message[0]
        position_message_serialized = position_message[1]
        position_message_deserialized = _deserialize_from_redis(position_message_serialized)
        position_message: PositionsChannel = PositionsChannel(**position_message_deserialized)
        position_messages.append(position_message)
    return position_messages


async def get_stream_order_messages(async_redis: aioredis.Redis, count: int = 10):
    order_messages_serialized = await async_redis.xrevrange('okx:messages@orders', count=count)
    if not order_messages_serialized:
        print(f"orders information not ready in order cache!")
        return []

    order_messages_serialized.reverse()

    order_messages = []
    for order_message in order_messages_serialized:
        redis_stream_id = order_message[0]
        order_message_serialized = order_message[1]
        order_message_deserialized = _deserialize_from_redis(order_message_serialized)
        order_message : OrdersChannel = OrdersChannel(**order_message_deserialized)
        order_messages.append(order_message)
    return order_messages

