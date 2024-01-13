import uvicorn
from fastapi import FastAPI

from routers.api_keys import api_key_router
from routers.login import login_router
from routers.okx import okx_router
from routers.okx_authentication import okx_authentication_router

app = FastAPI(
    title="AntBot-Rest-API",
    description="",
    version="1.0.0",
)
websocket_task = None

app.include_router(login_router)
app.include_router(okx_router)
app.include_router(api_key_router)
app.include_router(okx_authentication_router)

# app.include_router(websockets_router)

# async def start_websocket():
#     try:
#         import os
#         await okx_websockets_main_run(
#             apikey=os.getenv('OKX_API_KEY'),
#             passphrase=os.getenv('OKX_PASSPHRASE'),
#             secretkey=os.getenv('OKX_SECRET_KEY'),
#             sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
#             input_channel_models=[
#                 MarkPriceChannelInputArgs(channel="mark-price", instId="BTC-USDT-240329")
#             ]
#         )
#     except Exception as e:
#         print(f"WebSocket Error: {e}")
#         #TODO Implement your reconnection logic here
#
#
# @app.on_event("startup")
# async def startup_event():
#     global websocket_task
#     websocket_task = asyncio.create_task(start_websocket())
#
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     if websocket_task:
#         websocket_task.cancel()
#         try:
#             await websocket_task
#         except asyncio.CancelledError:
#             print("WebSocket task was cancelled")
#     else:
#         print("WebSocket task was not running")


if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.0", port=8080)
    # uvicorn.run(app="main:app", host="127.0.0.0", port=8080, reload=True)
