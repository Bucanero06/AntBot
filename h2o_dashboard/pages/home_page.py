import asyncio

from h2o_wave import main, Q, app, ui, on,run_on, data # noqa F401

from h2o_dashboard.util import clear_cards, add_card, stream_message


async def homepage(q: Q):
    print("Loading homepage")
    await q.run(clear_cards, q, ignore=['Application_Sidebar'])
