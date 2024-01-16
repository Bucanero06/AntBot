import asyncio

import dotenv
import uvicorn
from fastapi import FastAPI

from pyokx.websocket_handling import okx_websockets_main_run
from pyokx.ws_data_structures import *

app = FastAPI(
    title="AntBot-Websocket-API",
    description="",
    version="1.0.0",
)
websocket_task = None

dotenv.load_dotenv(dotenv.find_dotenv())


async def start_websocket():
    try:
        import os
        import redis
        from redis_tools.syncio.store import Store
        from redis_tools.config import RedisConfig
        await okx_websockets_main_run(input_channel_models=[
            ### Public Channels
            InstrumentsChannelInputArgs(channel="instruments", instType="FUTURES"),

            ### Private Channels
            AccountChannelInputArgs(channel="account", ccy=None),
            PositionChannelInputArgs(channel="positions", instType="FUTURES",
                                     instFamily=None,
                                     instId=None
                                     ),
            BalanceAndPositionsChannelInputArgs(channel="balance_and_position"),
            OrdersChannelInputArgs(channel="orders", instType="FUTURES", instFamily=None, instId=None)
        ], apikey=os.getenv('OKX_API_KEY'), passphrase=os.getenv('OKX_PASSPHRASE'),
            secretkey=os.getenv('OKX_SECRET_KEY'), sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
            redis_store=True
        )
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # TODO Implement your reconnection logic here


@app.on_event("startup")
async def startup_event():
    global websocket_task
    websocket_task = asyncio.create_task(start_websocket())


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


if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.0", port=8081)
    # uvicorn.run(app="main:app", host="127.0.0.0", port=8080, reload=True)
