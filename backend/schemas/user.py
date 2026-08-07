from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from schemas.picture import PictureInfo
from schemas.framily import Role


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None


class DeleteAccountRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserFramilyInfo(BaseModel):
    code: str
    name: Optional[str] = None
    role: Role
    member_count: int
    picture_count: int
    created_at: datetime


class UserInfo(BaseModel):
    username: str
    email: Optional[str] = None
    display_name: str
    created_at: Optional[datetime] = None
    framilies: list[UserFramilyInfo] = Field(default_factory=list)
    pictures: list[PictureInfo] = Field(default_factory=list)


class UserInfoResponse(BaseModel):
    user: UserInfo