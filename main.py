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
import uvicorn
from fastapi import FastAPI

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


@app.get("/health")
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
    # uvicorn.run(app="main:app", host="127.0.0.0", port=8080, reload=True)
