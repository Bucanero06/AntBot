import os
from pprint import pprint

import dotenv
import uvicorn
from fastapi import FastAPI

from firebase_tools.authenticate import authenticate_with_firebase
# from data.config import *
# from routers import *
# from model.todo import *
# from model.user import *
# from model.okx import *
from routers.api_keys import api_key_router
from routers.login import login_router
from routers.okx import okx_router

app = FastAPI(
    title="AntBot-Rest-API",
    description="",
    version="1.0.0",
)

# app.include_router(signup_router)
app.include_router(login_router)
# app.include_router(user_router)
# app.include_router(todo_router)
app.include_router(okx_router)
app.include_router(api_key_router)


if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.0", port=8080)
    # uvicorn.run(app="main:app", host="127.0.0.0", port=8080, reload=True)
