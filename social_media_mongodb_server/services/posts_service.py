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

            # --- NEW: merge nested author info + remove duplicate field ---
            author = c.pop("author", None)
            if isinstance(author, dict):
                # Ensure username stays in the top-level field you already use
                c["author_username"] = author.get("username", c.get("author_username"))

                # Optionally expose avatar from users collection
                if author.get("avatar_url"):
                    c["author_avatar_url"] = author["avatar_url"]

            comments.append(c)
        result["comments"] = comments
    return result

async def list_posts_service(db, skip: int = 0, limit: int = 0):
    # author_id=None → all posts
    rows = await list_posts(db, skip=skip, limit=limit, author_id=None)
    out = []
    for p in rows:
        p = mongo_obj_to_dict(p)
        p["author_id"] = str(p["author_id"]) if p.get("author_id") else None

        # author_username and author_avatar_url are already simple types
        # If "author" ever sneaks in, flatten and drop it
        author = p.pop("author", None)
        if isinstance(author, dict):
            if "username" in author and "author_username" not in p:
                p["author_username"] = author["username"]
            if "avatar_url" in author and "author_avatar_url" not in p:
                p["author_avatar_url"] = author["avatar_url"]

        out.append(p)
    return out

async def list_user_posts_service(db, user_id: str, skip: int = 0, limit: int = 0):
    """
    List posts for a specific user (author), using the same aggregation pipeline.
    """
    rows = await list_posts(db, skip=skip, limit=limit, author_id=user_id)
    out = []
    for p in rows:
        p = mongo_obj_to_dict(p)
        p["author_id"] = str(p["author_id"]) if p.get("author_id") else None

        author = p.pop("author", None)
        if isinstance(author, dict):
            if "username" in author and "author_username" not in p:
                p["author_username"] = author["username"]
            if "avatar_url" in author and "author_avatar_url" not in p:
                p["author_avatar_url"] = author["avatar_url"]

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
