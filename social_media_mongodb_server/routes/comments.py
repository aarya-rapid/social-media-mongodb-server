from fastapi import APIRouter, Depends, HTTPException, status
from ..models.comment_models import CommentCreate, CommentUpdate, CommentInDB
from ..services.comments_service import create_comment_service, list_comments_service, update_comment_service, delete_comment_service
from ..routes.auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/posts", tags=["Comments"])  # comments endpoints nested under posts

@router.post("/{post_id}/comments", response_model=CommentInDB, status_code=status.HTTP_201_CREATED)
async def create_comment_endpoint(post_id: str, comment: CommentCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    created, err_code, err_msg = await create_comment_service(db, current_user, post_id, comment)
    if err_code:
        raise HTTPException(status_code=err_code, detail=err_msg)
    return created

@router.get("/{post_id}/comments", response_model=list[CommentInDB])
async def list_comments_endpoint(post_id: str, db=Depends(get_db)):
    return await list_comments_service(db, post_id)

@router.get("/comments/{comment_id}", response_model=CommentInDB)
async def get_comment_endpoint(comment_id: str, db=Depends(get_db)):
    from ..repositories.comments_repo import get_comment
    comment = await get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = __import__("social_media_mongodb_server.utils.helpers", fromlist=["mongo_obj_to_dict"]).mongo_obj_to_dict(comment)
    comment["post_id"] = str(comment["post_id"])
    comment["author_id"] = str(comment["author_id"]) if comment.get("author_id") else None
    return comment

@router.put("/comments/{comment_id}", response_model=CommentInDB)
async def update_comment_endpoint(comment_id: str, comment_update: CommentUpdate, db=Depends(get_db), current_user=Depends(get_current_user)):
    updated, err_code, err_msg = await update_comment_service(db, current_user, comment_id, comment_update)
    if err_code:
        raise HTTPException(status_code=err_code, detail=err_msg)
    return updated

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_endpoint(comment_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    code, msg = await delete_comment_service(db, current_user, comment_id)
    if code != 204:
        raise HTTPException(status_code=code, detail=msg)
    return
