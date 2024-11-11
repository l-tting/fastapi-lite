from passlib.context import CryptContext
from models import User
from database import sessionlocal
from fastapi import Depends,HTTPException
from datetime import datetime,timedelta,timezone
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import jwt,ExpiredSignatureError,JWTError
import uuid

SECRET_KEY ='1kslll3o3l'
ALGORITHM ='HS256'
ACCESS_TOKEN_EXPIRY_TIME = 30
# ACCESS_TOKEN_EXPIRY_TIME = 3600


pwd_context = CryptContext(schemes=['bcrypt'],deprecated="auto")

def check_user(email):
    db = sessionlocal()
    user = db.query(User).filter(User.email==email).first()
    return user

def create_token(data:dict,expries_delta:timedelta | None=None):
    to_encode = data.copy()
    if expries_delta:
        expires = datetime.now(timezone.utc) + expries_delta
    else:
        expires = datetime.now(timezone.utc) + expries_delta(seconds=30)
    to_encode.update({"exp":expires})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

    return encoded_jwt

def get_token_auth_heaaders(credentials:HTTPAuthorizationCredentials=Depends(HTTPBearer())):
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=403,detail="Invalid authentication scheme")
    
    return credentials.credentials
    

async def get_current_user(token: str = Depends(get_token_auth_heaaders)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('user')
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = check_user(email)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")
    
    return user

