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
import threading

import dotenv
import uvicorn
from fastapi import FastAPI, APIRouter

from pyokx.rest_messages_service import okx_rest_messages_services
from pyokx.websocket_handling import okx_websockets_main_run
from pyokx.ws_data_structures import AccountChannelInputArgs, PositionsChannelInputArgs, \
    BalanceAndPositionsChannelInputArgs, OrdersChannelInputArgs
from redis_tools.utils import init_async_redis, stop_async_redis

app = FastAPI(
    title="AntBot-Websocket-API",
    description="",
    version="2.0.0",
)
websocket_task = None
rest_task = None
# websocket_instrument_task = None # need to have per instrument
websocket_instrument_task = None

dotenv.load_dotenv(dotenv.find_dotenv())

'''
----------------------------------------------------
                   APP Startup 
----------------------------------------------------
'''


@app.get("/health")
def health_check():
    # Todo add more health check metrics used around the codebase
    return {"status": "OK"}

def start_websocket_task_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(okx_websockets_main_run(input_channel_models=[
        ### Private Channels
        AccountChannelInputArgs(channel="account", ccy=None,
                                extraParams="{"
                                            "\"updateInterval\": \"1\""
                                            "}"),
        PositionsChannelInputArgs(channel="positions", instType="ANY", instFamily=None, instId=None,
                                  extraParams="{"
                                              "\"updateInterval\": \"1\""
                                              "}"),
        BalanceAndPositionsChannelInputArgs(channel="balance_and_position"),
        OrdersChannelInputArgs(channel="orders", instType="FUTURES", instFamily=None, instId=None)
    ], apikey=os.getenv('OKX_API_KEY'), passphrase=os.getenv('OKX_PASSPHRASE'),
        secretkey=os.getenv('OKX_SECRET_KEY'), sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
        redis_store=True
    ))
    loop.close()
@app.on_event("startup")
async def startup_event():
    print("Startup event triggered")
    global websocket_task
    global rest_task
    global websocket_instrument_task

    async_redis = await init_async_redis()
    assert async_redis, "async_redis is None, check the connection to the Redis server"

    websocket_thread = threading.Thread(target=start_websocket_task_loop)
    websocket_thread.start()
    rest_task = asyncio.create_task(okx_rest_messages_services(reload_interval=30))

    # TODO need to do this for each desired instrument and should be updated since contracts expire thus
    #  instruments change
    # websocket_instrument_task = asyncio.create_task(start_instrument_websocket(
    #     input_channel_models=
    #     get_instrument_specific_channel_inputs_to_listen_to() +
    #                          get_btc_usdt_usd_index_channel_inputs_to_listen_to()
    # ))


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutdown event triggered")
    if websocket_task:
        websocket_task.cancel()
        try:
            await websocket_task
        except asyncio.CancelledError:
            print("WebSocket task was cancelled")
    else:
        print("WebSocket task was not running")

    if rest_task:
        rest_task.cancel()
        try:
            await rest_task
        except asyncio.CancelledError:
            print("REST task was cancelled")
    else:
        print("REST task was not running")

    if websocket_instrument_task:
        websocket_instrument_task.cancel()
        try:
            await websocket_instrument_task
        except asyncio.CancelledError:
            print("WebSocket task was cancelled")

    await stop_async_redis()


'''
----------------------------------------------------
                   API ROUTERS 
----------------------------------------------------
'''
websocket_router = APIRouter(tags=["websocket"], include_in_schema=False)


@websocket_router.get("/restart_instrument_websocket")
async def restart_instrument_websocket():  # Todo adds security for now dont expose
    return {"status": "failed", "message": "Endpoint not enabled implemented yet"}
    global websocket_instrument_task
    # turn down the websocket
    if websocket_instrument_task:
        websocket_instrument_task.cancel()
        try:
            await websocket_instrument_task
        except asyncio.CancelledError:
            print("WebSocket task was cancelled")
    else:
        print("WebSocket task was not running")

    # turn up the websocket
    # TODO need to do this for each desired instrument and should be updated since contracts expire thus
    #  instruments change
    # websocket_instrument_task = asyncio.create_task(start_instrument_websocket(
    #     input_channel_models=
    #     get_instrument_specific_channel_inputs_to_listen_to() +
    #                          get_btc_usdt_usd_index_channel_inputs_to_listen_to()
    # ))
    return {"status": "success", "message": "Restarted instrument websocket"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.0", port=8080)
