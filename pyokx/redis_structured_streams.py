from typing import List

import aioredis

from pyokx.websocket_handling import available_channel_models
from pyokx.ws_data_structures import AccountChannel, PositionChannel
from redis_tools.utils import _deserialize_from_redis

'''Structured Messages Stream'''


async def get_stream_all_messages(async_redis: aioredis.Redis, count: int = 10):
    messages_serialized = await async_redis.xrange('okx:messages@all', count=count)
    if not messages_serialized:
        print(f"no messages in all cache!")
        return []

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
    """Uses xrange to get the latest COUNT account messages from redis and return all COUNT messages"""
    account_messages_serialized = await async_redis.xrange('okx:messages@account', count=count)
    if not account_messages_serialized:
        print(f"account information not ready in account cache!")
        return []

    account_messages = []
    for account_message in account_messages_serialized:
        redis_stream_id = account_message[0]
        account_message_serialized = account_message[1]
        account_message_deserialized = _deserialize_from_redis(account_message_serialized)
        account_message: AccountChannel = AccountChannel(**account_message_deserialized)
        account_messages.append(account_message)
    return account_messages


async def get_stream_position_messages(async_redis: aioredis.Redis, count: int = 10) -> List[PositionChannel]:
    """Uses xrange to get the latest COUNT position messages from redis and return all COUNT messages"""
    position_messages_serialized = await async_redis.xrange('okx:messages@position', count=count)
    if not position_messages_serialized:
        print(f"position information not ready in position cache!")
        return []

    position_messages = []
    for position_message in position_messages_serialized:
        redis_stream_id = position_message[0]
        position_message_serialized = position_message[1]
        position_message_deserialized = _deserialize_from_redis(position_message_serialized)
        position_message: PositionChannel = PositionChannel(**position_message_deserialized)
        position_messages.append(position_message)
    return position_messages
