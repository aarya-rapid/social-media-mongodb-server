from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from ..models.post_models import PostCreate, PostUpdate, PostWithComments, PostInDB
from ..services.posts_service import get_post_with_comments, list_posts_service, create_post_service, update_post_service, delete_post_service
from ..routes.auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.get("/", response_model=list[PostInDB])
async def list_posts_endpoint(skip: int = 0, limit: int = 0, db=Depends(get_db)):
    return await list_posts_service(db, skip=skip, limit=limit)

@router.post("/", response_model=PostInDB, status_code=status.HTTP_201_CREATED)
async def create_post_endpoint(post: PostCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    created = await create_post_service(db, current_user, post)
    return created

@router.get("/{post_id}", response_model=PostWithComments)
async def get_post_endpoint(post_id: str,
                            include_comments: Optional[bool] = Query(True),
                            comments_limit: Optional[int] = Query(None, ge=1),
                            comments_skip: Optional[int] = Query(0, ge=0),
                            db=Depends(get_db)):
    result = await get_post_with_comments(db, post_id, include_comments, comments_limit, comments_skip)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return result

@router.put("/{post_id}", response_model=PostInDB)
async def update_post_endpoint(post_id: str, post_update: PostUpdate, db=Depends(get_db), current_user=Depends(get_current_user)):
    updated, err_code, err_msg = await update_post_service(db, current_user, post_id, post_update)
    if err_code:
        raise HTTPException(status_code=err_code, detail=err_msg)
    return updated

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_endpoint(post_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    code, msg = await delete_post_service(db, current_user, post_id)
    if code != 204:
        raise HTTPException(status_code=code, detail=msg)
    return
