from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from firebase_tools.BaseClasses import FirebaseAuthGoodResponse
from firebase_tools.authenticate import authenticate_with_firebase
from routers.api_keys import create_access_token
from shared.config import DEFAULT_KEY_EXPIRE_TIME

login_router = APIRouter(tags=["Token"], include_in_schema=False)


@login_router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(request: OAuth2PasswordRequestForm = Depends(),
          # db: Session = Depends(get_db)
          ):
    # login_user = db.query(User).filter(request.username == User.email).first()
    # if not login_user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                         detail="{} does not exist".format(request.username)
    #                         )
    # if not pwd_context.verify(request.password, login_user.password):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    #                         detail="incorrect password"
    #                         )

    response = authenticate_with_firebase(request.username, request.password)
    print(response)
    if response['status'] != 'success':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=response['error_message']
                            )

    good_response = FirebaseAuthGoodResponse(**response)

    token = create_access_token(data={"sub": good_response.email,
                                      "id": good_response.user_id,
                                      "role": 'user'
                                      },
                                expires_delta=timedelta(minutes=DEFAULT_KEY_EXPIRE_TIME)
                                )

    return {"access_token": token, "token_type": "bearer"}
