from datetime import datetime, timedelta
import os
from fastapi import APIRouter, HTTPException, Depends
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from dotenv import load_dotenv

from .models import UserCreate, UserInDB
from .users import create_user, get_user_by_email, verify_password
from . import db as db_module

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
async def register(user: UserCreate):
    db_module.connect_to_mongo()
    new_user = await create_user(user)
    return {"message": "User created", "user_id": new_user["id"]}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db_module.connect_to_mongo()
    user = await get_user_by_email(form_data.username)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        user["id"] = str(user["_id"])
        user.pop("password", None)  # remove password before returning
        return UserInDB(**user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
