from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserInDB(BaseModel):
    id: str
    email: EmailStr
    username: str
