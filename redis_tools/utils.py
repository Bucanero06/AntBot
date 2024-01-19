import json
import os
from enum import Enum

import aioredis
import redis


def _serialize_for_redis(data):
    if isinstance(data, Enum):
        return data.name  # or data.value if you want to store the value
    elif isinstance(data, dict):
        return {k: _serialize_for_redis(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_for_redis(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(_serialize_for_redis(item) for item in data)
    elif data is None:
        return ""
    else:
        return data


def serialize_for_redis(model_dict):
    message_dict = dict()
    for key, value in model_dict.items():
        message_dict[key] = _serialize_for_redis(value)
    return {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
            for k, v in message_dict.items()}


def _deserialize_from_redis(data):
    if isinstance(data, str):
        try:
            # Attempt to deserialize JSON
            return json.loads(data)
        except json.JSONDecodeError:
            # If not a valid JSON, assume it's a simple string
            return data
    elif isinstance(data, dict):
        return {k: _deserialize_from_redis(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_deserialize_from_redis(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(_deserialize_from_redis(item) for item in data)
    elif isinstance(data, Enum):
        # Handle Enum deserialization
        # Assuming Enums are stored as strings
        return data[data]
    else:
        return data


async def connect_to_aioredis():
    async_redis = None
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

    return async_redis


def connect_to_redis():
    sync_redis = None
    try:
        host = 'localhost'
        sync_redis = redis.from_url(f"redis://{host}:6379", decode_responses=True)
        sync_redis.ping()

    except Exception as e:
        print(f"Redis Error: {e}")
        try:
            host = os.getenv('REDIS_HOST', "redis")
            sync_redis = redis.from_url(f"redis://{host}:6379", decode_responses=True)
            sync_redis.ping()
        except Exception as e:
            print(f"Redis Error: {e}")

    return sync_redis
