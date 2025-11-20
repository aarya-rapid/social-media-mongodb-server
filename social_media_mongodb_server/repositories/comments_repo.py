from bson import ObjectId

async def create_comment(db, doc: dict):
    res = await db["comments"].insert_one(doc)
    return await db["comments"].find_one({"_id": res.inserted_id})

async def get_comment(db, comment_id: str):
    return await db["comments"].find_one({"_id": ObjectId(comment_id)})

async def update_comment(db, comment_id: str, update: dict):
    await db["comments"].update_one({"_id": ObjectId(comment_id)}, {"$set": update})
    return await db["comments"].find_one({"_id": ObjectId(comment_id)})

async def delete_comment(db, comment_id: str):
    return await db["comments"].delete_one({"_id": ObjectId(comment_id)})

async def list_comments_for_post(db, post_id: str, skip: int = 0, limit: int = 0):
    cursor = db["comments"].find({"post_id": ObjectId(post_id)}).sort("created_at", 1)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    results = []
    async for c in cursor:
        results.append(c)
    return results
