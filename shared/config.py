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
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import dotenv
dotenv.load_dotenv(dotenv.find_dotenv())

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
DEFAULT_KEY_EXPIRE_TIME = int(os.getenv('DEFAULT_KEY_EXPIRE_TIME', 3600))

assert SECRET_KEY, f'{SECRET_KEY = }'
assert ALGORITHM, f'{ALGORITHM = }'
assert DEFAULT_KEY_EXPIRE_TIME, f'{DEFAULT_KEY_EXPIRE_TIME = }'



Base = declarative_base()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
