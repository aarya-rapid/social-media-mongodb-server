from datetime import datetime
from typing import Optional

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


# ---------- POST MODELS ----------

class PostBase(BaseModel):
    title: str = Field(..., example="My first post")
    content: str = Field(..., example="Hello, world!")


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PostInDB(PostBase):
    id: str
    created_at: datetime
    updated_at: datetime


# ---------- COMMENT MODELS ----------

class CommentBase(BaseModel):
    author: str = Field(..., example="Aarya")
    content: str = Field(..., example="Nice post!")


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    author: Optional[str] = None
    content: Optional[str] = None


class CommentInDB(CommentBase):
    id: str
    post_id: str
    created_at: datetime
    updated_at: datetime
