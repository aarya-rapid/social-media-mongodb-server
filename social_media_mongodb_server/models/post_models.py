from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., example="My first post")
    content: str = Field(..., example="Hello world")

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostInDB(PostBase):
    id: str
    created_at: datetime
    updated_at: datetime
    author_id: Optional[str] = None
    author_username: Optional[str] = None

class PostWithComments(BaseModel):
    post: PostInDB
    comments: List[dict] = []
