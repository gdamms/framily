from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r'^[a-zA-Z0-9_.-]+$')
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterResponse(BaseModel):
    token: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str
    remember_me: bool = True


class LoginResponse(BaseModel):
    token: str


class UserInfo(BaseModel):
    username: str
    email: str | None = None
    display_name: str

    class Config:
        from_attributes = True
