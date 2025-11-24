from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from another_fastapi_jwt_auth import AuthJWT

from ..models.user_models import UserCreate
from ..services.auth_service import register_user, authenticate_user, create_access_token, decode_token
from ..db import get_db
from ..repositories.users_repo import get_user_by_id

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db=Depends(get_db)):
    try:
        created = await register_user(db, user)
        return {"message": "User created", "user_id": created["id"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    Authorize: AuthJWT = Depends(),
    db = Depends(get_db),
):
    # Your existing username/email + password verification
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # subject -> we store user id; could also store email instead
    subject = user["id"]  # make sure your authenticate_user returns id as string
    # Optionally add extra claims
    access_token = Authorize.create_access_token(
        subject=subject,
        user_claims={
            "email": user["email"],
            "username": user["username"],
        },
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

# helper dependency to get current user
async def get_current_user(
    Authorize: AuthJWT = Depends(),
    db = Depends(get_db),
):
    # This is where the "middleware" feeling comes in: jwt_required()
    # reads Authorization header and validates the token.
    Authorize.jwt_required()  # raises AuthJWTException on failure

    user_id = Authorize.get_jwt_subject()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Normalize id field for the rest of your code
    user["id"] = str(user["_id"])
    return user
