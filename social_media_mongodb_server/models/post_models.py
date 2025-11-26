from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., example="My first post")
    content: str = Field(..., example="Hello world")
    image_url: Optional[HttpUrl] = None
    image_prompt: Optional[str] = None
    image_provider: Optional[str] = None  # e.g. "flux-imagegen-mcp"

class PostCreate(PostBase):
    # pass
    generate_image: bool = False   # optional flag
    image_prompt: Optional[str] = None

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