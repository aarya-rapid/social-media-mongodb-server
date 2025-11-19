import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "social_media_db")

client: AsyncIOMotorClient | None = None
db = None


def connect_to_mongo():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
        db_name = (MONGODB_DB_NAME or "social_media_db").strip()
        db = client[db_name]
        print(f"Connected to MongoDB at {MONGODB_URI}, db={db_name}")


def close_mongo_connection():
    global client, db
    if client is not None:
        client.close()
        client = None
        db = None
        print("Closed MongoDB connection")
