from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from ..models.user_models import UserCreate
from ..services.auth_service import register_user, authenticate_user, create_access_token, decode_token
from ..db import get_db

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
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    # OAuth2 expects 'username' field for login; we use email in that field.
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(subject=user["email"])
    return {"access_token": token, "token_type": "bearer"}

# helper dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from jose import JWTError
    from ..repositories.users_repo import get_user_by_email
    try:
        sub = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    user = await get_user_by_email(db, sub)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user["id"] = str(user["_id"])
    user.pop("password", None)
    return user
