from datetime import datetime
from ..repositories.posts_repo import get_post_by_id, create_post, update_post, delete_post, list_posts
from ..repositories.comments_repo import list_comments_for_post
from ..utils.helpers import mongo_obj_to_dict

async def get_post_with_comments(db, post_id: str, include_comments: bool = True, limit: int = None, skip: int = 0):
    post = await get_post_by_id(db, post_id)
    if not post:
        return None
    post = mongo_obj_to_dict(post)
    post["author_id"] = str(post["author_id"]) if post.get("author_id") else None
    result = {"post": post, "comments": []}
    if include_comments:
        rows = await list_comments_for_post(db, post_id, skip=skip, limit=limit or 0)
        comments = []
        for c in rows:
            c = mongo_obj_to_dict(c)
            c["post_id"] = str(c["post_id"])
            c["author_id"] = str(c["author_id"]) if c.get("author_id") else None
            comments.append(c)
        result["comments"] = comments
    return result

async def list_posts_service(db, skip: int = 0, limit: int = 0):
    rows = await list_posts(db, skip=skip, limit=limit)
    out = []
    for p in rows:
        p = mongo_obj_to_dict(p)
        p["author_id"] = str(p["author_id"]) if p.get("author_id") else None
        out.append(p)
    return out

async def create_post_service(db, current_user, post_create):
    now = datetime.utcnow()
    doc = {
        "title": post_create.title,
        "content": post_create.content,
        "created_at": now,
        "updated_at": now,
        "author_id": __import__("bson").ObjectId(current_user["id"]),
        "author_username": current_user["username"],
    }
    created = await create_post(db, doc)
    created = mongo_obj_to_dict(created)
    created["author_id"] = str(created["author_id"]) if created.get("author_id") else None
    return created

async def update_post_service(db, current_user, post_id: str, post_update):
    post = await get_post_by_id(db, post_id)
    if not post:
        return None, 404, "Post not found"
    if "author_id" not in post or str(post["author_id"]) != current_user["id"]:
        return None, 403, "Not authorized"
    update_data = {k: v for k, v in post_update.dict(exclude_unset=True).items()}
    if not update_data:
        return None, 400, "No fields to update"
    update_data["updated_at"] = datetime.utcnow()
    updated = await update_post(db, post_id, update_data)
    updated = mongo_obj_to_dict(updated)
    updated["author_id"] = str(updated["author_id"]) if updated.get("author_id") else None
    return updated, None, None

async def delete_post_service(db, current_user, post_id: str):
    post = await get_post_by_id(db, post_id)
    if not post:
        return 404, "Post not found"
    if "author_id" not in post or str(post["author_id"]) != current_user["id"]:
        return 403, "Not authorized"
    await delete_post(db, post_id)
    return 204, None
