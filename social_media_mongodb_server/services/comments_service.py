import asyncio
from datetime import datetime
from ..repositories.comments_repo import create_comment, get_comment, update_comment, delete_comment, list_comments_for_post
from ..repositories.posts_repo import get_post_by_id
from ..repositories.users_repo import get_user_by_id  # ensure this exists (we added earlier)
from ..utils.helpers import mongo_obj_to_dict
from ..utils.sendgrid_utils import send_email_sync  # blocking helper

async def create_comment_service(db, current_user, post_id: str, comment_create):
    # Verify post exists
    post = await get_post_by_id(db, post_id)
    if not post:
        return None, 404, "Post not found"

    now = datetime.utcnow()
    doc = {
        "post_id": __import__("bson").ObjectId(post_id),
        "content": comment_create.content,
        "created_at": now,
        "updated_at": now,
        "author_id": __import__("bson").ObjectId(current_user["id"]),
        "author_username": current_user["username"],
    }
    created = await create_comment(db, doc)
    created = mongo_obj_to_dict(created)
    created["post_id"] = str(created["post_id"])
    created["author_id"] = str(created["author_id"]) if created.get("author_id") else None

    # --- Send notification email to post author (non-blocking) ---
    try:
        # fetch post author details
        author_id = post.get("author_id")
        if author_id:
            author = await get_user_by_id(db, str(author_id))
            # user document might not have email if created before adding email field
            author_email = author.get("email") if author else None
            # do not notify commenter themselves
            commenter_email = current_user.get("email")
            if author_email and author_email != commenter_email:
                # build post link (APP_BASE_URL from env)
                from os import getenv
                base_url = getenv("APP_BASE_URL", "http://127.0.0.1:8000")
                post_link = f"{base_url}/posts/{post_id}"

                # Example HTML content - include the uploaded image as a URL
                uploaded_file_url = "/mnt/data/99122be6-e5c4-4dd5-bcdb-804c3d8e3f53.png"  # local path provided earlier
                html = f"""
                <p>Hi {author.get('username', 'there')},</p>
                <p><strong>{current_user['username']}</strong> commented on your post "<em>{post.get('title','(untitled)')}</em>".</p>
                <p>Comment: {comment_create.content}</p>
                <p><a href="{post_link}">View the post</a></p>
                <p>Attached is a local file (dev): <code>{uploaded_file_url}</code></p>
                <hr/>
                <p>— Your App</p>
                """

                plain = f"{current_user['username']} commented on your post: {comment_create.content}\nView: {post_link}"

                # run blocking send in a thread so we don't block event loop
                try:
                    asyncio.create_task(asyncio.to_thread(send_email_sync, author_email,
                                                         f"New comment on your post: {post.get('title','')}",
                                                         html, plain, uploaded_file_url))
                except Exception:
                    # if create_task/to_thread not available for any reason, call in a fallback thread
                    await asyncio.to_thread(send_email_sync, author_email,
                                           f"New comment on your post: {post.get('title','')}",
                                           html, plain, uploaded_file_url)
    except Exception:
        # swallow exceptions from notification so comment creation remains successful
        pass

    return created, None, None


async def list_comments_service(db, post_id: str, skip: int = 0, limit: int = 0):
    rows = await list_comments_for_post(db, post_id, skip=skip, limit=limit)
    out = []
    for c in rows:
        c = mongo_obj_to_dict(c)
        c["post_id"] = str(c["post_id"])
        c["author_id"] = str(c["author_id"]) if c.get("author_id") else None
        out.append(c)
    return out

async def update_comment_service(db, current_user, comment_id: str, comment_update):
    comment = await get_comment(db, comment_id)
    if not comment:
        return None, 404, "Comment not found"
    if "author_id" not in comment or str(comment["author_id"]) != current_user["id"]:
        return None, 403, "Not authorized"
    update_data = {k: v for k, v in comment_update.dict(exclude_unset=True).items()}
    if not update_data:
        return None, 400, "No fields to update"
    update_data["updated_at"] = datetime.utcnow()
    updated = await update_comment(db, comment_id, update_data)
    updated = mongo_obj_to_dict(updated)
    updated["post_id"] = str(updated["post_id"])
    updated["author_id"] = str(updated["author_id"]) if updated.get("author_id") else None
    return updated, None, None

async def delete_comment_service(db, current_user, comment_id: str):
    comment = await get_comment(db, comment_id)
    if not comment:
        return 404, "Comment not found"
    if "author_id" not in comment or str(comment["author_id"]) != current_user["id"]:
        return 403, "Not authorized"
    await delete_comment(db, comment_id)
    return 204, None
