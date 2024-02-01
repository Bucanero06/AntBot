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
from fastapi import APIRouter, Depends, HTTPException, status
from schema.user import UserScheme, ShowUser
from sqlalchemy.orm import Session
from data.config import get_db, pwd_context
from model.user import *

# signup_router = APIRouter(tags=["Signup"], include_in_schema=True)


# @signup_router.post("/Register",
#                    status_code=status.HTTP_201_CREATED,
#                    response_model=ShowUser)
# async def create_user(request: UserScheme, db: Session = Depends(get_db)):
async def create_user(request: UserScheme, db: Session = Depends(get_db)):
    new_user = User(name=request.name,
                    email=request.email.lower(),
                    age=request.age,
                    password=pwd_context.hash(request.password),
                    role="normal"
                    )

    if not db.query(User).first():
        new_user.role = "admin"

    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="the email {} already exists!".format(request.email)
        )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
