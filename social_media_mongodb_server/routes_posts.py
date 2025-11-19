from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

# IMPORTANT: import the *module*, not `db` directly
from . import db as db_module
from .models import (
    PostCreate,
    PostUpdate,
    PostInDB,
    CommentCreate,
    CommentUpdate,
    CommentInDB,
    mongo_obj_to_dict,
    to_object_id,
)

router = APIRouter(prefix="/posts", tags=["Posts"])


# Dependency to get the DB
async def get_db():
    if db_module.db is None:
        db_module.connect_to_mongo()
    if db_module.db is None:
        # Extra safety: if something went wrong
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_module.db


# ---------- POSTS CRUD ----------

@router.post(
    "/",
    response_model=PostInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(post: PostCreate, database=Depends(get_db)):
    now = datetime.utcnow()
    doc = {
        "title": post.title,
        "content": post.content,
        "created_at": now,
        "updated_at": now,
    }
    result = await database["posts"].insert_one(doc)
    created = await database["posts"].find_one({"_id": result.inserted_id})
    return PostInDB(**mongo_obj_to_dict(created))


@router.get("/", response_model=List[PostInDB])
async def list_posts(database=Depends(get_db)):
    posts_cursor = database["posts"].find().sort("created_at", -1)
    posts: list[PostInDB] = []
    async for post in posts_cursor:
        posts.append(PostInDB(**mongo_obj_to_dict(post)))
    return posts


@router.get("/{post_id}", response_model=PostInDB)
async def get_post(post_id: str, database=Depends(get_db)):
    _id = to_object_id(post_id)
    post = await database["posts"].find_one({"_id": _id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostInDB(**mongo_obj_to_dict(post))


@router.put("/{post_id}", response_model=PostInDB)
async def update_post(post_id: str, post_update: PostUpdate, database=Depends(get_db)):
    _id = to_object_id(post_id)
    update_data = {k: v for k, v in post_update.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await database["posts"].update_one({"_id": _id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")

    post = await database["posts"].find_one({"_id": _id})
    return PostInDB(**mongo_obj_to_dict(post))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, database=Depends(get_db)):
    _id = to_object_id(post_id)

    # Delete comments for this post first
    await database["comments"].delete_many({"post_id": _id})

    result = await database["posts"].delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return


# ---------- COMMENTS (per post) ----------

@router.post(
    "/{post_id}/comments",
    response_model=CommentInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment_for_post(
    post_id: str, comment: CommentCreate, database=Depends(get_db)
):
    post_obj_id = to_object_id(post_id)

    post = await database["posts"].find_one({"_id": post_obj_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    now = datetime.utcnow()
    doc = {
        "post_id": post_obj_id,
        "author": comment.author,
        "content": comment.content,
        "created_at": now,
        "updated_at": now,
    }
    result = await database["comments"].insert_one(doc)
    created = await database["comments"].find_one({"_id": result.inserted_id})

    created = mongo_obj_to_dict(created)
    created["post_id"] = str(created["post_id"])
    return CommentInDB(**created)


@router.get(
    "/{post_id}/comments",
    response_model=List[CommentInDB],
)
async def list_comments_for_post(post_id: str, database=Depends(get_db)):
    post_obj_id = to_object_id(post_id)

    comments_cursor = database["comments"].find({"post_id": post_obj_id}).sort(
        "created_at", 1
    )

    comments: list[CommentInDB] = []
    async for comment in comments_cursor:
        comment = mongo_obj_to_dict(comment)
        comment["post_id"] = str(comment["post_id"])
        comments.append(CommentInDB(**comment))
    return comments


# ---------- COMMENT BY ID ----------

@router.get("/comments/{comment_id}", response_model=CommentInDB)
async def get_comment(comment_id: str, database=Depends(get_db)):
    _id = to_object_id(comment_id)
    comment = await database["comments"].find_one({"_id": _id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment = mongo_obj_to_dict(comment)
    comment["post_id"] = str(comment["post_id"])
    return CommentInDB(**comment)


@router.put("/comments/{comment_id}", response_model=CommentInDB)
async def update_comment(
    comment_id: str, comment_update: CommentUpdate, database=Depends(get_db)
):
    _id = to_object_id(comment_id)
    update_data = {k: v for k, v in comment_update.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await database["comments"].update_one({"_id": _id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment = await database["comments"].find_one({"_id": _id})
    comment = mongo_obj_to_dict(comment)
    comment["post_id"] = str(comment["post_id"])
    return CommentInDB(**comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: str, database=Depends(get_db)):
    _id = to_object_id(comment_id)
    result = await database["comments"].delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    return
