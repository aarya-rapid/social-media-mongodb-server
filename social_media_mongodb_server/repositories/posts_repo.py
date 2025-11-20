from bson import ObjectId

async def get_post_by_id(db, post_id: str):
    return await db["posts"].find_one({"_id": ObjectId(post_id)})

async def list_posts(db, skip: int = 0, limit: int = 0):
    cursor = db["posts"].find().sort("created_at", -1)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
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
