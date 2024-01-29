import asyncio

import dotenv
import uvicorn
from fastapi import FastAPI, APIRouter

from pyokx.websocket_handling import okx_websockets_main_run
from pyokx.ws_data_structures import *

app = FastAPI(
    title="AntBot-Websocket-API",
    description="",
    version="2.0.0",
)
websocket_task = None
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


@app.on_event("startup")
async def startup_event():
    global websocket_task
    global websocket_instrument_task

    websocket_task = asyncio.create_task(start_websocket())

    # TODO need to do this for each desired instrument and should be updated since contracts expire thus
    #  instruments change
    # websocket_instrument_task = asyncio.create_task(start_instrument_websocket(
    #     input_channel_models=
    #     get_instrument_specific_channel_inputs_to_listen_to() +
    #                          get_btc_usdt_usd_index_channel_inputs_to_listen_to()
    # ))


@app.on_event("shutdown")
async def shutdown_event():
    if websocket_task:
        websocket_task.cancel()
        try:
            await websocket_task
        except asyncio.CancelledError:
            print("WebSocket task was cancelled")
    else:
        print("WebSocket task was not running")

    if websocket_instrument_task:
        websocket_instrument_task.cancel()
        try:
            await websocket_instrument_task
        except asyncio.CancelledError:
            print("WebSocket task was cancelled")


async def start_websocket():
    try:
        import os
        await okx_websockets_main_run(input_channel_models=[
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
        )
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # TODO Implement your reconnection logic here


async def start_instrument_websocket(input_channel_models: list):
    try:
        import os
        await okx_websockets_main_run(input_channel_models=input_channel_models, apikey=os.getenv('OKX_API_KEY'),
                                      passphrase=os.getenv('OKX_PASSPHRASE'),
                                      secretkey=os.getenv('OKX_SECRET_KEY'),
                                      sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
                                      redis_store=True
                                      )
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # TODO Implement your reconnection logic here


'''
----------------------------------------------------
                   API ROUTERS 
----------------------------------------------------
'''
websocket_router = APIRouter(tags=["websocket"], include_in_schema=False)


@websocket_router.get("/restart_instrument_websocket")
async def restart_instrument_websocket():  # Todo adds security for now dont expose
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
    uvicorn.run(app=app, host="127.0.0.0", port=8081)
    # uvicorn.run(app="main:app", host="127.0.0.0", port=8080, reload=True)
