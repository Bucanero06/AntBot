import asyncio
import os

import dotenv
from h2o_wave import main, Q, app, ui, on, data, run_on  # noqa F401

from h2o_dashboard.redis_connection import  start_redis, stop_redis
from h2o_dashboard.wave_auth import initialize_client, serve_security

dotenv.load_dotenv(dotenv.find_dotenv())


@on('global_notification_bar.dismissed')
async def on_global_notification_bar_dismissed(q: Q):
    # Delete the notification bar
    q.page['meta'].notification_bar = None
    await q.page.save()


async def on_startup():
    await start_redis()


async def on_shutdown():
    await stop_redis()


@app('/', on_startup=on_startup, on_shutdown=on_shutdown)
async def serve(q: Q):
    """Main application handler."""
    print("Serving")
    if not q.client.initialized:
        print("Initializing")
        await initialize_client(q)
        q.client.homepage_running_event = asyncio.Event()
        q.client.okx_debug_page_running_event = asyncio.Event()
        if not q.app.initialized:  # TODO this could be instantiated each client? and shut down after each use?
            await start_redis()

        from h2o_dashboard import async_redis
        q.client.async_redis = async_redis

    if not (os.getenv('BYPASS_SECURITY') == 'True' and os.getenv('DEVELOPMENT_GOD_MODE') == 'True'):
        bypass_security = False
    else:
        bypass_security = True

    await serve_security(q, bypass_security=bypass_security),

    await q.page.save()
    await run_on(q)

    print("Served")
