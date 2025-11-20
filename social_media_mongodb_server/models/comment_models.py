from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentCreate(BaseModel):
    content: str = Field(..., example="Nice post!")

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentInDB(BaseModel):
    id: str
    post_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    author_id: Optional[str] = None
    author_username: Optional[str] = None
