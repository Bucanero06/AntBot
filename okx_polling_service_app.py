import asyncio

import dotenv
import uvicorn
from fastapi import FastAPI

from pyokx.rest_messages_service import okx_rest_messages_services
from redis_tools.utils import init_async_redis, stop_async_redis
from shared.logging import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="AntBot-OKX-REST-Service",
    description="",
    version="2.0.0",
)
rest_task = None
# websocket_instrument_task = None # need to have per instrument

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
    logger.info("Startup event triggered")
    global rest_task
    global websocket_instrument_task

    async_redis = await init_async_redis()
    assert async_redis, "async_redis is None, check the connection to the Redis server"

    rest_task = asyncio.create_task(okx_rest_messages_services(slow_reload_interval=30))


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutdown event triggered")
    if rest_task:
        rest_task.cancel()
        try:
            await rest_task
        except asyncio.CancelledError:
            logger.error("REST task was cancelled")
    else:
        logger.warning("REST task was not running")

    await stop_async_redis()


'''
----------------------------------------------------
                   API ROUTERS 
----------------------------------------------------
'''

if __name__ == "__main__":
    uvicorn.run(app="okx_polling_service_app:app", host="127.0.0.0", port=8080)
