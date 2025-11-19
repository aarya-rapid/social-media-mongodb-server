import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "social_media_db")

client: AsyncIOMotorClient | None = None
db = None


def _ensure_indexes(database):
    """
    Create important indexes:
     - users.email unique
     - posts.created_at descending (for sorting)
     - comments: compound index (post_id, created_at)
    """
    # users.email unique
    database["users"].create_index("email", unique=True)

    # posts.created_at for fast sorting
    database["posts"].create_index([("created_at", DESCENDING)])

    # comments: index on post_id then created_at for listing comments per post
    database["comments"].create_index([("post_id", ASCENDING), ("created_at", ASCENDING)])


def connect_to_mongo():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
        db_name = (MONGODB_DB_NAME or "social_media_db").strip()
        db = client[db_name]
        # Ensure indexes (this uses PyMongo synchronous create_index calls under motor)
        try:
            _ensure_indexes(db)
            print("Indexes created/ensured")
        except Exception as e:
            print("Warning: error creating indexes:", e)
        print(f"Connected to MongoDB at {MONGODB_URI}, db={db_name}")


def close_mongo_connection():
    global client, db
    if client is not None:
        client.close()
        client = None
        db = None
        print("Closed MongoDB connection")
