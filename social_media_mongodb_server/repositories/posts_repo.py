from bson import ObjectId
from typing import Optional, List

async def get_post_by_id(db, post_id: str):
    return await db["posts"].find_one({"_id": ObjectId(post_id)})

async def list_posts(
    db,
    skip: int = 0,
    limit: int = 0,
    author_id: Optional[str] = None,
):
    """
    List posts using MongoDB aggregation.

    - Optional filter by author_id
    - Sorts by created_at DESC (newest first)
    - Applies skip/limit for pagination
    - Looks up author details from users collection
    """
    pipeline: List[dict] = []

    # Optional filter for a specific author
    if author_id:
        try:
            author_obj_id = ObjectId(author_id)
        except Exception:
            # If invalid ObjectId, return empty list
            return []
        pipeline.append({"$match": {"author_id": author_obj_id}})

    # Sort newest → oldest
    pipeline.append({"$sort": {"created_at": -1}})

    # Pagination
    if skip:
        pipeline.append({"$skip": skip})
    if limit:
        pipeline.append({"$limit": limit})

    # Join with users collection to fetch author details
    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "author_id",
                    "foreignField": "_id",
                    "as": "author",
                }
            },
            {
                "$unwind": {
                    "path": "$author",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            # Shape the final document; keep it compatible with existing code
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "content": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "image_url": 1,
                    "image_prompt": 1,
                    "image_provider": 1,
                    "author_id": 1,
                    # if you already store author_username on the post, prefer that
                    "author_username": {
                        "$ifNull": ["$author_username", "$author.username"]
                    },
                    # extra field for convenience (optional)
                    "author_avatar_url": "$author.avatar_url",
                    # include any other post fields you use (tags, images, etc.)
                }
            },
        ]
    )

    cursor = db["posts"].aggregate(pipeline)
    results = []
    async for p in cursor:
        results.append(p)
    return results

async def create_post(db, doc: dict):
    res = await db["posts"].insert_one(doc)
    return await db["posts"].find_one({"_id": res.inserted_id})

async def update_post(db, post_id: str, update: dict):
    await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$set": update})
    return await db["posts"].find_one({"_id": ObjectId(post_id)})

async def delete_post(db, post_id: str):
    # delete comments first
    await db["comments"].delete_many({"post_id": ObjectId(post_id)})
    return await db["posts"].delete_one({"_id": ObjectId(post_id)})

async def set_post_image(
    db,
    post_id: str,
    image_url: str,
    prompt: str,
    provider: str = "flux-imagegen-mcp",
):
    await db["posts"].update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": {
                "image_url": image_url,
                "image_prompt": prompt,
                "image_provider": provider,
            }
        },
    )
    return await db["posts"].find_one({"_id": ObjectId(post_id)})
