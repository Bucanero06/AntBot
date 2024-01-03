from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from firebase_tools.authenticate import authenticate_with_firebase, check_token_validity
from pyokx.entry_way import instrument_searcher, clean_and_verify_instID
from shared.config import EXPIRE_TIME, SECRET_KEY, ALGORITHM

api_key_router = APIRouter(tags=["Token"], include_in_schema=True)

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from datetime import datetime, timedelta


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if isinstance(expires_delta, timedelta):
        expire = datetime.utcnow() + timedelta(minutes=EXPIRE_TIME)
        to_encode.update({"exp": expire})
    elif expires_delta:
        raise ValueError("expires_delta must be instance of timedelta")

    jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return jwt_token


class InstIdAPIKeyCreationRequestForm(BaseModel):
    username: str
    password: str
    instID: str
    expire_time: Optional[int] = None


class FirebaseAuthGoodResponse(BaseModel):
    status: str
    error_message: Optional[str]
    token: Optional[str]
    refresh_token: Optional[str]
    user_id: Optional[str]
    email: Optional[str]
    expires_in: Optional[str]


@api_key_router.post("/api_key", status_code=status.HTTP_202_ACCEPTED)
def create_instrument_api_key(request: InstIdAPIKeyCreationRequestForm = Depends(),
                              current_user=Depends(check_token_validity),
                              # current_user=Depends(check_token_validity),
                              # db: Session = Depends(get_db)
                              ):
    # login_user = db.query(User).filter(request.username == User.email).first()

    # if not login_user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                         detail="{} does not exist".format(request.username)
    #                         )

    response = authenticate_with_firebase(request.username, request.password)
    print(response)
    if response['status'] != 'success':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=response['error_message']
                            )

    good_response = FirebaseAuthGoodResponse(**response)

    # if not pwd_context.verify(request.password, good_response.token):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    #                         detail="incorrect token password"
    #                         )

    # Check whether the instID is valid
    instID = request.instID.upper()
    splitted = instID.split('-')
    assert len(splitted) == 3, f'The Futures instrument ID must be in the format of "BTC-USDT-210326". {instID = }'
    instrument = instrument_searcher.find_by_instId(instID)
    assert instrument is not None, f'Instrument {instID} not found in instrument_searcher'
    from pyokx.data_structures import InstType
    assert instrument.instType == InstType.FUTURES, f'Instrument {instID} is not a Futures instrument'

    token = create_access_token(data={"sub": good_response.email,
                                      "id": good_response.user_id,
                                      "role": 'trading_instrument',
                                      "instID": request.instID,
                                      },
                                expires_delta=timedelta(minutes=request.expire_time) if request.expire_time else None
                                )

    return {"access_token": token, "token_type": "bearer"}


def check_token_against_instrument(token: str, reference_instID: str,
                                   # db: Session = Depends(get_db)
                                   ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )

    reference_instID = clean_and_verify_instID(reference_instID)

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

    # check if the user has access to the instrument
    # user = db.query(User).filter(User.user_id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                         detail="user with This id {}, does not exist!".format(
    #                             user_id)
    #                         )

    # Todo add instIds to the user model
    # if instID not in user.instIDs:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    #                         detail="user with This id {}, does not have access to this instrument!".format(
    #                             user_id)
    #                         )
    assert role == 'trading_instrument', f'role must be "trading_instrument", {role = }'
    assert instID is not None, f'{instID = }'
    instID = clean_and_verify_instID(instID)
    assert instID == reference_instID, f'{instID = } != {reference_instID = }'

    return True
