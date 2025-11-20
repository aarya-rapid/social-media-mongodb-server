# DB connection and index creation (async)
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "social_media_db")

client: AsyncIOMotorClient | None = None
db = None

def get_mongo_client():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
    return client

async def connect_to_mongo():
    """
    Connects and ensures indexes. Call from startup event.
    """
    global client, db
    if client is None:
        client = get_mongo_client()
    db_name = (MONGODB_DB_NAME or "social_media_db").strip()
    db = client[db_name]

    # Create indexes asynchronously
    try:
        # users.email unique
        await db["users"].create_index("email", unique=True)
        # posts.created_at desc
        await db["posts"].create_index([("created_at", DESCENDING)])
        # comments: post_id + created_at
        await db["comments"].create_index([("post_id", ASCENDING), ("created_at", ASCENDING)])
        print("Indexes created/ensured")
    except Exception as e:
        print("Warning creating indexes:", e)

async def close_mongo_connection():
    global client, db
    if client:
        client.close()
        client = None
        db = None
        print("Closed MongoDB connection")

# dependency for routes
def get_db():
    if db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo on startup.")
    return db
