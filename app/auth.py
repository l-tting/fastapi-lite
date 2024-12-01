from passlib.context import CryptContext
from .models import User
from .database import sessionlocal
from fastapi import Depends,HTTPException,Request
from datetime import datetime,timedelta,timezone
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import jwt,ExpiredSignatureError,JWTError
import uuid

SECRET_KEY ='1kslll3o3l'
ALGORITHM ='HS256'
ACCESS_TOKEN_EXPIRY_TIME = timedelta(minutes=30)

# provides convinient way for hashind and verifying passwords
pwd_context = CryptContext(schemes=['bcrypt'],deprecated="auto")

def check_user(email):
    db = sessionlocal()
    user = db.query(User).filter(User.email==email).first()
    return user

def create_access_token(data:dict,expries_delta:timedelta | None=None):
    # create copy to avoid modifying original data
    to_encode = data.copy()
    if expries_delta:
        expires = datetime.now(timezone.utc) + expries_delta
    else:
        expires = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRY_TIME
    to_encode.update({"exp":expires})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

    return encoded_jwt

def create_refresh_token(data:dict,expires_delta:timedelta | None=None):
    to_encode = data.copy()
    if expires_delta:
        expires = datetime.now(timezone.utc) + expires_delta
    else:
        expires = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp":expires})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt
        

# def get_token_auth_heaaders(credentials:HTTPAuthorizationCredentials=Depends(HTTPBearer())):
#     if credentials.scheme != "Bearer":
#         raise HTTPException(status_code=403,detail="Invalid authentication scheme")
    
#     return credentials.credentials

# -> str specifies return type of the func
#func call in every request to ensure cookie is present
def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")  # Extract token from cookies
    if not token:
        raise HTTPException(status_code=401, detail="Access token missing from cookies")
    return token

def get_refresh_token(request:Request) ->str:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401,detail="Refresh token missing from cookies")
    return token

#Depends-means the dependency is executed first before handler
async def get_current_user(access_token: str = Depends(get_token_from_cookie)):
    try:
    # ALGORITHM passed in a list coz jwt.decode() can accept a list of algos for verification
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
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

def verify_refresh_token(refresh_token:str=Depends(get_refresh_token)):
    try:
        payload = jwt.decode(refresh_token,SECRET_KEY,algorithms=[ALGORITHM])
        email = payload.get('user')
        if email is None:
            raise HTTPException(status_code=401,detail='Could not validate credentails')
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401,detail='Refresh token expired')
    except JWTError:
        raise HTTPException(status_code=401,detail="Inavlid token")
    user = check_user(email)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")
    
