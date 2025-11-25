# social_media_mongodb_server/routes/mcp_proxy.py
from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..config import settings
from ..db import get_db
from ..models.mcp_models import MCPCommentCreate
from ..models.comment_models import CommentCreate, CommentInDB
from ..services.comments_service import create_comment_service
from ..routes.auth import get_current_user  # wherever your get_current_user is

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/comments", response_model=CommentInDB)
async def mcp_add_comment(
    payload: MCPCommentCreate,
    db=Depends(get_db),
    x_mcp_api_key: str = Header(None, alias="X-MCP-API-Key"),
    current_user=Depends(get_current_user),
):
    # 1) Check MCP API key
    if not x_mcp_api_key:
    # or x_mcp_api_key != settings.MCP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MCP API key",
        )

    # 2) Build the CommentCreate object
    comment_create = CommentCreate(content=payload.content)

    # 3) Reuse your existing comment service
    created, err_code, err_msg = await create_comment_service(
        db=db,
        current_user=current_user,       # real user from JWT
        post_id=payload.post_id,
        comment_create=comment_create,
    )

    if not created:
        raise HTTPException(
            status_code=err_code or 400,
            detail=err_msg or "Unable to create comment",
        )

    return created
