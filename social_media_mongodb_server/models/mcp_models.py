# social_media_mongodb_server/models/mcp_models.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class MCPCommentCreate(BaseModel):
    post_id: str
    content: str
    external_user_id: str | None = None
    external_username: str | None = None
    external_email: EmailStr | None = None

class ImageGenRequest(BaseModel):
    prompt: Optional[str] = None