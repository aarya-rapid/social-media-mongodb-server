from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from . import db as db_module
from .models import (
    PostCreate, PostUpdate, PostInDB,
    CommentCreate, CommentUpdate, CommentInDB,
    mongo_obj_to_dict, to_object_id
)
from .auth import get_current_user  # current_user will be UserInDB Pydantic model
from .models import PostWithComments

router = APIRouter(prefix="/posts", tags=["Posts"])

async def get_db():
    if db_module.db is None:
        db_module.connect_to_mongo()
    if db_module.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_module.db


# Create post (requires authentication)
@router.post("/", response_model=PostInDB, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    database=Depends(get_db),
    current_user=Depends(get_current_user),
):
    now = datetime.utcnow()
    author_obj_id = ObjectId(current_user.id)
    doc = {
        "title": post.title,
        "content": post.content,
        "created_at": now,
        "updated_at": now,
        "author_id": author_obj_id,
        "author_username": current_user.username,
    }
    result = await database["posts"].insert_one(doc)
    created = await database["posts"].find_one({"_id": result.inserted_id})
    # Convert author_id to string for API response
    created = mongo_obj_to_dict(created)
    created["author_id"] = str(created["author_id"])
    return PostInDB(**created)


# List posts (no change in authentication; returns author info if present)
@router.get("/", response_model=List[PostInDB])
async def list_posts(database=Depends(get_db)):
    posts_cursor = database["posts"].find().sort("created_at", -1)
    posts = []
    async for post in posts_cursor:
        post = mongo_obj_to_dict(post)
        post["author_id"] = str(post["author_id"]) if post.get("author_id") else None
        posts.append(PostInDB(**post))
    return posts


# # Get single post
# @router.get("/{post_id}", response_model=PostInDB)
# async def get_post(post_id: str, database=Depends(get_db)):
#     _id = to_object_id(post_id)
#     post = await database["posts"].find_one({"_id": _id})
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     post = mongo_obj_to_dict(post)
#     post["author_id"] = str(post["author_id"]) if post.get("author_id") else None
#     return PostInDB(**post)

# Get single post with comments
@router.get("/{post_id}", response_model=PostWithComments)
async def get_post_with_comments(
    post_id: str,
    include_comments: Optional[bool] = Query(
        True, description="Include comments in the response"
    ),
    comments_limit: Optional[int] = Query(
        None, ge=1, description="Limit the number of comments returned"
    ),
    comments_skip: Optional[int] = Query(
        0, ge=0, description="Number of comments to skip for pagination"
    ),
    database=Depends(get_db),
):
    """Return a single post plus its comments by default."""
    _id = to_object_id(post_id)

    # ---- Fetch post ----
    post = await database["posts"].find_one({"_id": _id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Convert Mongo document to API-friendly dict
    post = mongo_obj_to_dict(post)
    post["author_id"] = str(post["author_id"]) if post.get("author_id") else None

    comments_result = []

    # ---- Fetch comments (optional + paginated) ----
    if include_comments:
        cursor = (
            database["comments"]
            .find({"post_id": _id})
            .sort("created_at", 1)
        )

        if comments_skip:
            cursor = cursor.skip(int(comments_skip))

        if comments_limit:
            cursor = cursor.limit(int(comments_limit))

        async for c in cursor:
            c = mongo_obj_to_dict(c)
            c["post_id"] = str(c["post_id"])
            c["author_id"] = str(c["author_id"]) if c.get("author_id") else None
            comments_result.append(c)

    # Build response
    return {
        "post": post,
        "comments": comments_result
    }

# Update post (only owner)
@router.put("/{post_id}", response_model=PostInDB)
async def update_post(
    post_id: str,
    post_update: PostUpdate,
    database=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _id = to_object_id(post_id)
    post = await database["posts"].find_one({"_id": _id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Ownership check
    if "author_id" not in post or str(post["author_id"]) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")

    update_data = {k: v for k, v in post_update.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()
    await database["posts"].update_one({"_id": _id}, {"$set": update_data})
    updated = await database["posts"].find_one({"_id": _id})
    updated = mongo_obj_to_dict(updated)
    updated["author_id"] = str(updated["author_id"])
    return PostInDB(**updated)


# Delete post (only owner)
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    database=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _id = to_object_id(post_id)
    post = await database["posts"].find_one({"_id": _id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if "author_id" not in post or str(post["author_id"]) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    await database["comments"].delete_many({"post_id": _id})
    await database["posts"].delete_one({"_id": _id})
    return


# Create comment (auth required)
@router.post("/{post_id}/comments", response_model=CommentInDB, status_code=status.HTTP_201_CREATED)
async def create_comment_for_post(
    post_id: str,
    comment: CommentCreate,
    database=Depends(get_db),
    current_user=Depends(get_current_user),
):
    post_obj_id = to_object_id(post_id)
    post = await database["posts"].find_one({"_id": post_obj_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    now = datetime.utcnow()
    doc = {
        "post_id": post_obj_id,
        "content": comment.content,
        "created_at": now,
        "updated_at": now,
        "author_id": ObjectId(current_user.id),
        "author_username": current_user.username,
    }
    result = await database["comments"].insert_one(doc)
    created = await database["comments"].find_one({"_id": result.inserted_id})
    created = mongo_obj_to_dict(created)
    created["post_id"] = str(created["post_id"])
    created["author_id"] = str(created["author_id"])
    return CommentInDB(**created)


# List comments for a post
@router.get("/{post_id}/comments", response_model=List[CommentInDB])
async def list_comments_for_post(post_id: str, database=Depends(get_db)):
    post_obj_id = to_object_id(post_id)
    comments_cursor = database["comments"].find({"post_id": post_obj_id}).sort("created_at", 1)

    comments = []
    async for comment in comments_cursor:
        comment = mongo_obj_to_dict(comment)
        comment["post_id"] = str(comment["post_id"])
        comment["author_id"] = str(comment["author_id"])
        comments.append(CommentInDB(**comment))
    return comments


# Get single comment (no auth)
@router.get("/comments/{comment_id}", response_model=CommentInDB)
async def get_comment(comment_id: str, database=Depends(get_db)):
    _id = to_object_id(comment_id)
    comment = await database["comments"].find_one({"_id": _id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = mongo_obj_to_dict(comment)
    comment["post_id"] = str(comment["post_id"])
    comment["author_id"] = str(comment["author_id"])
    return CommentInDB(**comment)


# Update comment (only owner)
@router.put("/comments/{comment_id}", response_model=CommentInDB)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    database=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _id = to_object_id(comment_id)
    comment = await database["comments"].find_one({"_id": _id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if "author_id" not in comment or str(comment["author_id"]) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")

    update_data = {k: v for k, v in comment_update.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()
    await database["comments"].update_one({"_id": _id}, {"$set": update_data})
    updated = await database["comments"].find_one({"_id": _id})
    updated = mongo_obj_to_dict(updated)
    updated["post_id"] = str(updated["post_id"])
    updated["author_id"] = str(updated["author_id"])
    return CommentInDB(**updated)


# Delete comment (only owner)
@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    database=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _id = to_object_id(comment_id)
    comment = await database["comments"].find_one({"_id": _id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if "author_id" not in comment or str(comment["author_id"]) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    await database["comments"].delete_one({"_id": _id})
    return
