async def get_user_by_email(db, email: str):
    return await db["users"].find_one({"email": email})

async def get_user_by_id(db, user_id: str):
    from bson import ObjectId
    return await db["users"].find_one({"_id": ObjectId(user_id)})

async def create_user(db, doc: dict):
    res = await db["users"].insert_one(doc)
    return await db["users"].find_one({"_id": res.inserted_id})
