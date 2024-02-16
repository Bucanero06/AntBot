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

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from firebase_tools.BaseClasses import FirebaseAuthGoodResponse
from firebase_tools.authenticate import authenticate_with_firebase
from routers.api_keys import create_access_token
from shared.config import DEFAULT_KEY_EXPIRE_TIME

login_router = APIRouter(tags=["Token"], include_in_schema=False)


@login_router.post("/login", status_code=status.HTTP_202_ACCEPTED)
async def login(request: OAuth2PasswordRequestForm = Depends(),
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

    response = await authenticate_with_firebase(request.username, request.password)
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
