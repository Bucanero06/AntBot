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
    response = authenticate_with_firebase(request.username, request.password)
    print(response)
    if response['status'] != 'success':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=response['error_message']
                            )

    good_response = FirebaseAuthGoodResponse(**response)

    # Check whether the instID is valid
    instID = request.instID.upper()
    splitted = instID.split('-')
    assert len(splitted) == 3, f'The Futures instrument ID must be in the format of "BTC-USDT-210326". {instID = }'
    instrument_ticker = await _validate_instID_and_return_ticker_info(instID)
    assert instrument_ticker, f'Instrument {instID} not found in instrument_searcher'
    from pyokx.data_structures import InstType
    assert instrument_ticker.instType == 'FUTURES', \
        (f'Instrument {instID} is not a Futures instrument, type {instrument_ticker.instType}'
         f' rather than {InstType.FUTURES}')

    token = create_access_token(data={"sub": good_response.email,
                                      "id": good_response.user_id,
                                      "role": 'trading_instrument',
                                      "instID": request.instID,
                                      },
                                expires_delta=timedelta(minutes=request.expire_time) if request.expire_time else None
                                )

    return {"access_token": token, "token_type": "bearer"}
