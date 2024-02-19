
from typing import Optional

from fastapi import APIRouter
from shared.config import DEFAULT_KEY_EXPIRE_TIME, SECRET_KEY, ALGORITHM

api_key_router = APIRouter(tags=["Token"], include_in_schema=True)
from jose import jwt
from datetime import datetime, timedelta


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if isinstance(expires_delta, timedelta):
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_KEY_EXPIRE_TIME)
        to_encode.update({"exp": expire})
    elif expires_delta:
        raise ValueError("expires_delta must be instance of timedelta")

    jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return jwt_token
