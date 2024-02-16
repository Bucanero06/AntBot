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
import asyncio
import os

import dotenv
from h2o_wave import main, Q, app, ui, on, data, run_on  # noqa F401

from h2o_dashboard.wave_auth import initialize_client, serve_security
from redis_tools.utils import stop_async_redis, init_async_redis

dotenv.load_dotenv(dotenv.find_dotenv())


@on('global_notification_bar.dismissed')
async def on_global_notification_bar_dismissed(q: Q):
    # Delete the notification bar
    q.page['meta'].notification_bar = None
    await q.page.save()


async def on_startup():
    print("Startup event triggered")
    await init_async_redis()


async def on_shutdown():
    print("Shutdown event triggered")
    await stop_async_redis()


@on('@system.client_disconnect')
async def on_client_disconnect(q: Q):
    print('Client disconnected')
    # Pages Tasks and Events
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
            await init_async_redis()
            q.app.initialized = True

        q.client.async_redis = await init_async_redis()  # When already initializd it returns the connection

    if not (os.getenv('BYPASS_SECURITY') == 'True' and os.getenv('DEVELOPMENT_GOD_MODE') == 'True'):
        bypass_security = False
    else:
        bypass_security = True

    await serve_security(q, bypass_security=bypass_security),

    await q.page.save()
    await run_on(q)

    print("Served")
