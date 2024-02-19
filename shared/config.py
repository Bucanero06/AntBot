
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
