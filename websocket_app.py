import asyncio

import dotenv
import uvicorn
from fastapi import FastAPI

from pyokx.signal_handling import get_ticker_with_higher_volume
from pyokx.websocket_handling import okx_websockets_main_run
from pyokx.ws_data_structures import *

app = FastAPI(
    title="AntBot-Websocket-API",
    description="",
    version="1.0.0",
)
websocket_task = None
# websocket_instrument_task = None # need to have per instrument
websocket_instrument_task = None

dotenv.load_dotenv(dotenv.find_dotenv())


async def start_websocket():
    try:
        import os
        await okx_websockets_main_run(input_channel_models=[
            ### Private Channels
            AccountChannelInputArgs(channel="account", ccy=None),
            PositionChannelInputArgs(channel="positions", instType="ANY", instFamily=None, instId=None),
            BalanceAndPositionsChannelInputArgs(channel="balance_and_position"),
            OrdersChannelInputArgs(channel="orders", instType="FUTURES", instFamily=None, instId=None)
        ], apikey=os.getenv('OKX_API_KEY'), passphrase=os.getenv('OKX_PASSPHRASE'),
            secretkey=os.getenv('OKX_SECRET_KEY'), sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
            redis_store=True
        )
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # TODO Implement your reconnection logic here


def get_channel_inputs_to_listen_to():
    btc_ = get_ticker_with_higher_volume("BTC-USDT",
                                         instrument_type="FUTURES",
                                         top_n=1)
    eth_ = get_ticker_with_higher_volume("ETH-USDT",
                                         instrument_type="FUTURES",
                                         top_n=1)
    ltc = get_ticker_with_higher_volume("LTC-USDT",
                                        instrument_type="FUTURES",
                                        top_n=1)

    instruments_to_listen_to = btc_ + eth_ + ltc
    instrument_specific_channels = []

    for instrument in instruments_to_listen_to:
        instrument_specific_channels.append(OrderBookInputArgs(channel="books5", instId=instrument.instId))
        instrument_specific_channels.append(OrderBookInputArgs(channel="books", instId=instrument.instId))
        instrument_specific_channels.append(OrderBookInputArgs(channel="bbo-tbt", instId=instrument.instId))
        instrument_specific_channels.append(MarkPriceChannelInputArgs(channel="mark-price", instId=instrument.instId))
        instrument_specific_channels.append(TickersChannelInputArgs(channel="tickers", instId=instrument.instId))

    return instrument_specific_channels


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


@app.on_event("startup")
async def startup_event():
    global websocket_task
    global websocket_instrument_task

    websocket_task = asyncio.create_task(start_websocket())

    # TODO need to do this for each desired instrument and should be updated since contracts expire thus
    #  instruments change
    websocket_instrument_task = asyncio.create_task(start_instrument_websocket(
        input_channel_models=get_channel_inputs_to_listen_to())
    )


# Restart instrument websocker
@app.get("/restart_instrument_websocket")
async def restart_instrument_websocket():
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
    websocket_instrument_task = asyncio.create_task(start_instrument_websocket(
        input_channel_models=get_channel_inputs_to_listen_to(
            # todo add instrument settings to the input of the endpoint and pass them to the function
        ))
    )
    return {"status": "success", "message": "Restarted instrument websocket"}


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


if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.0", port=8081)
    # uvicorn.run(app="main:app", host="127.0.0.0", port=8080, reload=True)
