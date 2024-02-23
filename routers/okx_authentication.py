
from datetime import timedelta
from pprint import pprint
from typing import Optional

from fastapi import APIRouter, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel

from firebase_tools.BaseClasses import FirebaseAuthGoodResponse
from firebase_tools.authenticate import check_token_validity, authenticate_with_firebase
from pyokx.rest_handling import _validate_instID_and_return_ticker_info
from routers.api_keys import create_access_token
from shared.config import SECRET_KEY, ALGORITHM

okx_authentication_router = APIRouter(tags=["Token"], include_in_schema=True)

from fastapi import Depends, status


async def check_token_against_instrument(token: str, reference_instID: str,
                                   ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        reference_instID_ticker = await _validate_instID_and_return_ticker_info(reference_instID)
        assert reference_instID_ticker, f'{reference_instID = }'
        reference_instID = reference_instID_ticker.instId
    except AssertionError as e:
        reference_instID = ''
        print(f"AssertionError in check_token_against_instrument: {e}")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        instID: str = payload.get("instID")
        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception



    assert role == 'trading_instrument', f'role must be "trading_instrument", {role = }'
    assert instID is not None, f'{instID = }'
    instID_ticker = await _validate_instID_and_return_ticker_info(instID)
    assert instID_ticker, f'{instID = }'
    instID = instID_ticker.instId
    assert instID == reference_instID, f'{instID = } != {reference_instID = }'

    return True


class InstIdAPIKeyCreationRequestForm(BaseModel):
    username: str
    password: str
    instID: str
    expire_time: Optional[int] = None


@okx_authentication_router.post("/create_okx_instrument_api_key", status_code=status.HTTP_202_ACCEPTED)
async def create_instrument_api_key(request: InstIdAPIKeyCreationRequestForm = Depends(),
                              current_user=Depends(check_token_validity),
                              ):
    response = await authenticate_with_firebase(request.username, request.password)
    if response['status'] != 'success':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=response['error_message']
                            )

    good_response = FirebaseAuthGoodResponse(**response)

    # Check whether the instID is valid
    instID = request.instID.upper()
    instrument_ticker = await _validate_instID_and_return_ticker_info(instID)
    assert instrument_ticker, f'Instrument {instID} not found in instrument_searcher'

    token = create_access_token(data={"sub": good_response.email,
                                      "id": good_response.user_id,
                                      "role": 'trading_instrument',
                                      "instID": request.instID,
                                      },
                                expires_delta=timedelta(minutes=request.expire_time) if request.expire_time else None
                                )

    return {"access_token": token, "token_type": "bearer"}
