# social_media_mongodb_server/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Settings:
    def __init__(self) -> None:
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.SECRET_KEY = os.getenv(
            "SECRET_KEY",
            "dev-secret-change-me"  # change in prod
        )
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        # For MCP proxy requests
        self.MCP_API_KEY = os.getenv("MCP_API_KEY", "mcp-dev-key")

settings = Settings()
