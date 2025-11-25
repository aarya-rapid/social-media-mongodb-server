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
    from bson import ObjectId

    post_obj_id = ObjectId(post_id)

    pipeline = [
        {"$match": {"post_id": post_obj_id}},
        {"$sort": {"created_at": 1}},
    ]

    if skip:
        pipeline.append({"$skip": skip})
    if limit:
        pipeline.append({"$limit": limit})

    pipeline.extend([
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
        {
            "$project": {
                "_id": 1,
                "post_id": 1,
                "content": 1,
                "created_at": 1,
                "updated_at": 1,
                "author_id": 1,
                "author_username": 1,
                # Make nested author id a STRING, not ObjectId
                "author": {
                    "id": {"$toString": "$author._id"},
                    "username": "$author.username",
                    "avatar_url": "$author.avatar_url",
                },
            }
        },
    ])

    cursor = db["comments"].aggregate(pipeline)
    results = []
    async for c in cursor:
        results.append(c)
    return results

