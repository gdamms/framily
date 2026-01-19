from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str


class UserInfo(BaseModel):
    id: int
    username: str
    email: str | None = None
    display_name: str | None = None

    class Config:
        from_attributes = True
