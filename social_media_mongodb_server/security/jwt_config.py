# social_media_mongodb_server/security/jwt_config.py
import os
from pydantic import BaseModel
from another_fastapi_jwt_auth import AuthJWT
from dotenv import load_dotenv

# Load .env so SECRET_KEY is available when running locally
load_dotenv()

class AuthJWTSettings(BaseModel):
    # THIS NAME MUST BE EXACT: authjwt_secret_key
    authjwt_secret_key: str = os.getenv("SECRET_KEY")
    # Optional, but good to be explicit
    authjwt_algorithm: str = "HS256"

# This function is called by another-fastapi-jwt-auth to get settings
@AuthJWT.load_config
def get_config():
    return AuthJWTSettings()
