import asyncio
import os

from h2o_wave import main, Q, app, ui, on, data, run_on  # noqa F401

from h2o_dashboard.redis_refresh import refresh_redis, start_redis, stop_redis
from h2o_dashboard.wave_auth import initialize_client, serve_security


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
        if not q.app.initialized:
            await start_redis()
            (q.user.okx_account, q.user.okx_positions,
             q.user.okx_tickers, q.user.okx_orders, q.user.okx_balances_and_positions) = None, None, None, None, None
            q.user.okx_index_ticker = None
            await refresh_redis(q)

    if not (os.getenv('BYPASS_SECURITY') == 'True' and os.getenv('DEVELOPMENT_GOD_MODE') == 'True'):
        bypass_security = False
    else:
        bypass_security = True

    await asyncio.gather(
        serve_security(q, bypass_security=bypass_security),
        q.run(refresh_redis, q))

    await q.page.save()

    print("Served")
