'''Listen to Structured Websocket Streams

This module provides tools for setting up listeners for structured websocket streams,
processing incoming data, and managing the lifecycle of these listeners. It leverages
asyncio for asynchronous operations and integrates with FastAPI for web framework features.

Functions:
- add_listener_task: Add a new listener task to the global task registry.
- get_listener_task: Retrieve a listener task from the global task registry.
- remove_listener_task: Remove a listener task from the global task registry.
- get_all_listener_tasks: Retrieve all listener tasks from the global task registry.
- on_stream_data: Decorator for registering callback functions to specific redis streams.
- consumer: Asynchronous generator that consumes data from a specified stream.
- start_listening: Initialize listening tasks for provided streams and manage their lifecycle.
'''
import asyncio
from typing import List

from fastapi import HTTPException

from pyokx.ws_data_structures import available_channel_models
from redis_tools.utils import init_async_redis, deserialize_from_redis

callbacks = {}

listener_tasks = {}


def add_listener_task(task_key, listener_task, shutdown_signal_handler):
    '''
    Register a new listener task along with its shutdown signal handler.

    Parameters:
    - task_key (str): A unique identifier for the listener task.
    - listener_task (coroutine): The async task responsible for listening to the stream.
    - shutdown_signal_handler (function): A callable to be invoked during the shutdown process.

    This function does not return anything but updates the `listener_tasks` global dictionary.
    '''
    listener_tasks[task_key] = (listener_task, shutdown_signal_handler)


def get_listener_task(task_key):
    '''
    Retrieve a listener task by its unique identifier.

    Parameters:
    - task_key (str): The unique identifier of the listener task.

    Returns:
    - tuple: A tuple containing the listener task and its associated shutdown signal handler,
      or None if the task_key is not found.
    '''
    return listener_tasks.get(task_key)


def remove_listener_task(task_key):
    '''
    Remove a listener task from the global task registry.

    Parameters:
    - task_key (str): The unique identifier of the listener task to be removed.

    This function does not return anything but updates the `listener_tasks` global dictionary.
    '''
    if task_key in listener_tasks:
        del listener_tasks[task_key]


def get_all_listener_tasks():
    '''
    Retrieve all listener tasks from the global task registry.

    Returns:
    - dict: A dictionary of all registered listener tasks and their associated shutdown signal handlers.
    '''
    return listener_tasks


def on_stream_data(redis_stream):
    '''
    Decorator for registering callback functions to specific redis streams.

    Parameters:
    - redis_stream (str): The redis stream to which the callback functions are to be registered.

    Returns:
    - function: The decorator function that registers the provided callback to the specified stream.
    '''
    def decorator(callback_function):
        if redis_stream not in callbacks:
            callbacks[redis_stream] = []
        callbacks[redis_stream].append(callback_function)
        return callback_function

    return decorator


async def consumer(stream_name, shutdown_event, last_ids=None):
    '''
    Asynchronously consume messages from a specified stream and process them using registered callbacks.

    Parameters:
    - stream_name (str): The name of the stream to consume data from.
    - shutdown_event (asyncio.Event): An event to signal shutdown and cleanly stop the consumer.
    - last_ids (dict, optional): A dictionary to track the last processed message ID for each stream.

    This function is a coroutine and should be awaited. It runs indefinitely until a shutdown event is set.
    '''
    if last_ids is None:
        last_ids = {}
    async_redis = await init_async_redis()

    # Wait for initialization or other setup if necessary.
    await asyncio.sleep(3)

    # Use "$" as the special ID to only receive messages that are new to the stream
    last_id = last_ids.get(stream_name, "$")
    print(f'Listening to stream: {stream_name} with last_id: {last_id}')
    while not shutdown_event.is_set():
        # Read messages. Block=0 means it will return immediately if there are no messages.
        messages = await async_redis.xread(streams={stream_name: last_id}, block=0, count=1)
        for message in messages:
            _, message_entries = message
            for message_entry in message_entries:
                message_id, message_fields = message_entry
                message_serialized = message_fields.get("data")

                if not message_serialized:
                    print(
                        f"A message in the stream {stream_name} with id {message_id} was empty, skipping")
                    continue

                message_deserialized = deserialize_from_redis(message_serialized)
                message_channel = message_deserialized.get("arg").get("channel")
                data_struct = available_channel_models.get(message_channel)

                if not data_struct:
                    print(f"No data structure model available for channel: {message_channel}")
                    continue

                if hasattr(data_struct, "from_array"):
                    structured_message = data_struct.from_array(**message_deserialized)
                else:
                    structured_message = data_struct(**message_deserialized)

                if stream_name in callbacks:
                    for callback in callbacks[stream_name]:
                        # Ensure that the callback processing is awaited and sequential
                        await callback(structured_message)
                else:
                    print(f"No callbacks registered for stream: {stream_name}")

                # Update last_id to the current message's ID to ensure the next read gets new messages.
                last_id = message_id
                last_ids[stream_name] = last_id  # Update the last_ids dict with the new last_id for the stream

    # Clean up the connection
    await async_redis.close()


async def start_listening(streams: List[str], shutdown_event: asyncio.Event = None):
    '''
    Initialize and manage listening tasks for the provided streams.

    Parameters:
    - streams (List[str]): A list of stream names to start listening to.
    - shutdown_event (asyncio.Event, optional): An event to signal shutdown and cleanly stop all consumers.

    Returns:
    - task_key (str): A unique key representing the set of started listening tasks.

    Raises:
    - HTTPException: If listeners for the provided streams are already running.

    This function is a coroutine and should be awaited. It initializes consumer tasks for each provided stream.
    '''
    if not shutdown_event:
        shutdown_event = asyncio.Event()

    task_key = "_".join(sorted(streams))  # Unique key for the set of streams
    if task_key in listener_tasks:
        raise HTTPException(status_code=400, detail=f"Listeners for these streams are already running: {streams}")

    async def shutdown_signal_handler():
        shutdown_event.set()

    consumers = [consumer(stream_name, shutdown_event) for stream_name in streams]

    listener_task = asyncio.gather(*consumers)
    add_listener_task(task_key, listener_task, shutdown_signal_handler)

    return task_key
