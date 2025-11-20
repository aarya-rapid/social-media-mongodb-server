from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel, Field


# Helper type for ObjectId -> string
def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


def mongo_obj_to_dict(obj: dict) -> dict:
    """
    Convert a MongoDB document to a JSON-serializable dict.
    Renames _id -> id (string).
    """
    if not obj:
        return obj
    obj["id"] = str(obj["_id"])
    obj.pop("_id", None)
    return obj

# ---------- USER MODELS ----------

class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: str


# ---------- COMMENT MODELS ----------

class CommentBase(BaseModel):
    author: Optional[str] = None  # keep optional; we'll set actual author from current_user
    content: str = Field(..., example="Nice post!")

class CommentCreate(BaseModel):
    content: str

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentInDB(BaseModel):
    id: str
    post_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    author_id: str
    author_username: str



# ---------- POST MODELS ----------

class PostBase(BaseModel):
    title: str = Field(..., example="My first post")
    content: str = Field(..., example="Hello, world!")

class PostCreate(PostBase):
    # client does NOT supply author fields
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostInDB(PostBase):
    id: str
    created_at: datetime
    updated_at: datetime
    author_id: str
    author_username: str

class PostWithComments(BaseModel):
    post: PostInDB
    comments: List[CommentInDB] = []