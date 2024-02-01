"""A simple declarative ORM for redis based on pydantic.

Provides:

1. A subclass-able `Model` class to create Object Relational Mapping to
redis hashes
2. A redis `Store` class to mutate and query `Model`'s registered in it
3. A `RedisConfig` class to pass to the `Store` constructor to connect
to a redis instance
4. A synchronous `syncio` and an asynchronous `asyncio` interface to the
above classes
5. Parent-child relationships allowing for nesting models within models.
"""

async_redis = None


