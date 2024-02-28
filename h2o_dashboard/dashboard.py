
import asyncio
import os

import dotenv
from h2o_wave import main, Q, app, ui, on, data, run_on  # noqa F401

from h2o_dashboard.wave_auth import initialize_client, serve_security
from redis_tools.utils import stop_async_redis, get_async_redis

dotenv.load_dotenv(dotenv.find_dotenv())


@on('global_notification_bar.dismissed')
async def on_global_notification_bar_dismissed(q: Q):
    # Delete the notification bar
    q.page['meta'].notification_bar = None
    await q.page.save()


async def on_startup():
    print("Startup event triggered")
    await get_async_redis()


async def on_shutdown():
    print("Shutdown event triggered")
    await stop_async_redis()


@on('@system.client_disconnect')
async def on_client_disconnect(q: Q):
    print('Client disconnected')
    # Rest token
    q.client.initialized = False
    q.client.async_redis = None
    q.client.token = None
    q.client.user = None
    q.client.user_id = None
    q.client.email = None
    q.client.password = None
    q.client.expires_in = None

    # Pages Tasks and Events # Todo automate the handling of these to reduce developer error
    q.client.overview_page_running_event.clear()
    q.client.okx_dashboard_page_running_event.clear()
    q.client.documentation_page_running_event.clear()
    q.client.overview_page_task.cancel()
    q.client.okx_dashboard_page_task.cancel()
    q.client.documentation_page_task.cancel()

    # Redis Listener Tasks and Events
    q.client.okx_redis_listener_task.cancel()
    q.client.okx_redis_listener_running_event.clear()

    await asyncio.sleep(1)
    print('Client disconnected')


@app('/', on_startup=on_startup, on_shutdown=on_shutdown)
async def serve(q: Q):
    """Main application handler."""
    print("Serving")
    if not q.client.initialized:
        print("Initializing")
        await initialize_client(q)
        # First check if
        # are already initialized that way we either clear them or not initialize them again
        if not isinstance(getattr(q.client, 'overview_page_running_event'), asyncio.Event):
            q.client.overview_page_running_event = asyncio.Event()
        if not isinstance(getattr(q.client, 'okx_dashboard_page_running_event'), asyncio.Event):
            q.client.okx_dashboard_page_running_event = asyncio.Event()
        if not isinstance(getattr(q.client, 'documentation_page_running_event'), asyncio.Event):
            q.client.documentation_page_running_event = asyncio.Event()

        q.client.overview_page_running_event.clear()
        q.client.okx_dashboard_page_running_event.clear()
        q.client.documentation_page_running_event.clear()

        if not q.app.initialized:  # TODO this could be instantiated each client? and shut down after each use?
            await get_async_redis()
            q.app.initialized = True

        q.client.async_redis = await get_async_redis()  # When already initializd it returns the connection

    if not (os.getenv('BYPASS_SECURITY') == 'True' and os.getenv('DEVELOPMENT_GOD_MODE') == 'True'):
        bypass_security = False
    else:
        bypass_security = True

    await serve_security(q, bypass_security=bypass_security),

    await q.page.save()
    await run_on(q)

    print("Served")
