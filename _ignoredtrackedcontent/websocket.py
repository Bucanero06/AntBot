import os

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

from firebase_tools.authenticate import check_token_validity
from pyokx.websocket_handling import okx_websockets_main_run

websockets_router = APIRouter(tags=["WebsocketConnections"], include_in_schema=True)


@websockets_router.post("/start_okx_websocket/")
async def start_websocket(background_tasks: BackgroundTasks,
                          current_user=Depends(check_token_validity),
                          ):
    try:
        # Add WebSocket logic to background tasks
        from pyokx.ws_data_structures import MarkPriceChannelInputArgs
        background_tasks.add_task(okx_websockets_main_run,
                                  apikey=os.getenv('OKX_API_KEY'),
                                  passphrase=os.getenv('OKX_PASSPHRASE'),
                                  secretkey=os.getenv('OKX_SECRET_KEY'),
                                  sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
                                  input_channel_models=[
                                      MarkPriceChannelInputArgs(channel="mark-price", instId="BTC-USDT-240329")
                                  ])  # Add your channel models here
        return {"message": "WebSocket connection initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
