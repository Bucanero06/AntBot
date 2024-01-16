import asyncio

from h2o_wave import main, Q, app, ui, on, data, run_on  # noqa F401

from h2o_dashboard.redis_refresh import refresh_redis, start_redis, stop_redis
from h2o_dashboard.wave_auth import initialize_client, render_hidden_content


@on('global_notification_bar.dismissed')
async def on_global_notification_bar_dismissed(q: Q):
    # Delete the notification bar
    q.page['meta'].notification_bar = None
    await q.page.save()


async def on_startup():
    await start_redis()


async def on_shutdown():
    await stop_redis()

async def ping_okx_bot(q: Q):
    await asyncio.sleep(5)
    await ping_okx_bot(q)

@app('/', on_startup=on_startup, on_shutdown=on_shutdown)
async def serve(q: Q):
    """Main application handler."""
    print("Serving")
    if not q.client.initialized:
        print("Initializing")
        await initialize_client(q)
        if not q.app.initialized:
            await start_redis()
            q.user.okx_positions = []
            q.user.okx_balances = []
            q.user.okx_trades = []
            await refresh_redis(q)


    # await asyncio.gather(
    #     serve_security(q),
    #     q.run(refresh_redis, q))

    # # # FIXME DELETE VVVVVVV
    await asyncio.gather(
        render_hidden_content(q),
        q.run(refresh_redis, q))
    # # # FIXME DELETE ^^^^^^^

    await q.page.save()
    await run_on(q)
