import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv
from ..repositories.users_repo import get_user_by_email, create_user

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set in .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def _utf8_len(s: str) -> int:
    return len(s.encode("utf-8"))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def register_user(db, user_create):
    existing = await get_user_by_email(db, user_create.email)
    if existing:
        raise ValueError("User already exists")
    hashed = hash_password(user_create.password)
    doc = {"email": user_create.email, "username": user_create.username, "password": hashed}
    created = await create_user(db, doc)
    # remove password for return
    created["id"] = str(created["_id"])
    created.pop("password", None)
    return created

async def authenticate_user(db, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.get("password", "")):
        return None
    # return user dict with id string
    user["id"] = str(user["_id"])
    user.pop("password", None)
    return user

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise JWTError("Missing sub")
        return sub
    except JWTError as e:
        raise
