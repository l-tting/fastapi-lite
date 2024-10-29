from passlib.context import CryptContext
from models import User
from database import sessionlocal

SECRET_KEY ='1kslll3o3l'
ALGORITHM ='HS256'
ACCESS_TOKEN_EXPIRY_TIME = 30