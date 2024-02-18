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
import json
from enum import Enum

import redis
from pydantic import BaseModel

import dotenv
import os

from redis_tools.config import RedisConfig

dotenv.load_dotenv(dotenv.find_dotenv())

REDIS_SERVICE_PORT = int(os.getenv('REDIS_SERVICE_PORT', 6379))
REDIS_SERVICE_DB = int(os.getenv('REDIS_SERVICE_DB', 0))
REDIS_SERVICE_PASSWORD = os.getenv('REDIS_SERVICE_PASSWORD', None)


def _serialize_for_redis(data):
    if isinstance(data, Enum):
        return data.name  # or data.value if you want to store the value
    elif isinstance(data, dict):
        return {k: _serialize_for_redis(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_for_redis(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(_serialize_for_redis(item) for item in data)
    elif isinstance(data, BaseModel):
        return data.model_dump()
    elif data is None:
        return ""
    else:
        return data


def serialize_for_redis(model_dict):
    serialized_data = _serialize_for_redis(model_dict)
    return json.dumps(serialized_data)


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


import aioredis


async def connect_to_aioredis():
    async_redis = None

    # Define possible Redis hosts and ports
    local_redis = ('localhost', REDIS_SERVICE_PORT)
    docker_redis = ('redis', REDIS_SERVICE_PORT)
    # Add more tuples (host, port) for other scenarios

    redis_options = [local_redis, docker_redis]  # Add more options as needed

    for host, port in redis_options:
        try:
            #     encoding: Optional[str] = "utf-8"
            redis_config = RedisConfig(
                host=host,
                port=port,
                db=REDIS_SERVICE_DB,
                password=REDIS_SERVICE_PASSWORD,
                ssl=False,
                encoding="utf-8"
            )
            print(f"{redis_config.redis_url = }")

            # async_redis = aioredis.from_url(f"redis://{host}:{port}", decode_responses=True)
            async_redis = aioredis.from_url(redis_config.redis_url, decode_responses=True)
            await async_redis.ping()
            print(f"Connected to Redis at {host}:{port}")
            return async_redis  # Return as soon as a successful connection is made
        except Exception as e:
            print(f"Redis connection attempt to {host}:{port} failed: {e}")

    print("Unable to connect to Redis using any of the configured options.")
    return None


async def init_async_redis():
    from redis_tools import async_redis

    if isinstance(async_redis, aioredis.Redis):
        print("Async Redis connection already exists")
        return async_redis

    async_redis = await connect_to_aioredis()

    if not async_redis:
        raise Exception("Redis connection failed")

    import redis_tools
    redis_tools.async_redis = async_redis

    return async_redis


async def stop_async_redis():
    from redis_tools import async_redis
    if isinstance(async_redis, aioredis.Redis):
        await async_redis.close()
        print("Async Redis connection closed")
    else:
        print("No async Redis connection to close")
