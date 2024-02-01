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
