# social_media_mongodb_server/users.py
from passlib.context import CryptContext
from fastapi import HTTPException
from bson import ObjectId

# import module, not the `db` variable
from . import db as db_module
from .models import UserCreate

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


async def get_user_by_email(email: str):
    """
    Return raw user document (including password hash) used for authentication.
    If the database connection is not ready, raise a 500 error.
    """
    if db_module is None or db_module.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return await db_module.db["users"].find_one({"email": email})


async def create_user(user: UserCreate):
    """
    Create a new user. Raises 400 if user already exists.
    Returns the created user dict WITHOUT the password field.
    """
    if db_module is None or db_module.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    existing = await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password)

    doc = {
        "email": user.email,
        "username": user.username,
        "password": hashed_pw,
    }

    result = await db_module.db["users"].insert_one(doc)
    created = await db_module.db["users"].find_one({"_id": result.inserted_id})
    if created:
        created["id"] = str(created["_id"])
        created.pop("password", None)  # remove password before returning
    return created
