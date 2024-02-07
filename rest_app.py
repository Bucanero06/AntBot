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
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends

from firebase_tools.authenticate import check_token_validity
from redis_tools.consumers import start_listening, get_listener_task, remove_listener_task, get_all_listener_tasks

from redis_tools.utils import init_async_redis, stop_async_redis
from routers.api_keys import api_key_router
from routers.login import login_router
from routers.okx import okx_router
from routers.okx_authentication import okx_authentication_router

app = FastAPI(
    title="AntBot-Rest-API",
    description="",
    version="1.8.0",
)

'''
----------------------------------------------------
                   APP Startup 
----------------------------------------------------
'''


@app.post("/start_listening/", tags=["Redis Listeners"])
async def start_listening_endpoint(streams: List[str],
                                   current_user=Depends(check_token_validity)):
    try:
        task_key = await start_listening(streams)
        return {"message": "Listener started", "task_key": task_key}
    except HTTPException as e:
        return {"error": str(e.detail)}


@app.post("/stop_listening/", tags=["Redis Listeners"])
async def stop_listening_endpoint(task_key: str,
                                  current_user=Depends(check_token_validity)):
    task_info = get_listener_task(task_key)
    if not task_info:
        return {"error": "Listener not found"}

    listener_task, shutdown_signal_handler = task_info
    await shutdown_signal_handler()  # Trigger the shutdown event
    await listener_task  # Wait for the task to complete
    remove_listener_task(task_key)  # Remove the task from the dictionary

    return {"message": "Listener stopped"}


@app.get("/health", tags=["health"])
def health_check():
    # Todo add more health check metrics used around the codebase
    return {"status": "OK"}


@app.on_event("startup")
async def startup_event():
    print("Startup event triggered")
    await init_async_redis()


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutdown event triggered")
    for _, (listener_task, shutdown_signal_handler) in get_all_listener_tasks().items():
        await shutdown_signal_handler()  # Send shutdown signal to listeners
        try:
            await listener_task  # Wait for the listener to finish
        except asyncio.CancelledError:
            pass  # The task was cancelled, handle it gracefully if needed
        except Exception as e:
            print(f"Error while shutting down listener: {e}")

    await stop_async_redis()


'''
----------------------------------------------------
                   API ROUTERS 
----------------------------------------------------
'''
app.include_router(login_router)
app.include_router(okx_router)
app.include_router(api_key_router)
app.include_router(okx_authentication_router)

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.0", port=8080)
    # uvicorn.run(app="rest_app:app", host="127.0.0.0", port=8080, reload=True)
