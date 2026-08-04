from pydantic import BaseModel, Field
from typing import Literal, Optional, List

Orientation = Literal["0", "90", "180", "270"]


class FramilySettingsInfo(BaseModel):
    orientation: Orientation
    interval_minutes: int
    show_uploader_name: bool


class FramilyUpdateSettingsRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    orientation: Optional[Orientation] = None
    interval_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    show_uploader_name: Optional[bool] = None


class FramilyConnectRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class FramilyInviteRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    username: str


class FramilyJoinRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    accepted: bool


class FramilyLeaveRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class FramilyKickRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    username: str


class FramilyPromoteRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    username: str
    new_role: int = Field(..., ge=0, le=2)


class FramilyUserInfo(BaseModel):
    username: str
    display_name: Optional[str] = None
    role: int


class FramilyPictureInfo(BaseModel):
    id: str
    uploader_username: str


class FramilyInfoResponse(BaseModel):
    code: str
    name: Optional[str]
    members: List[FramilyUserInfo] = Field(default_factory=list)
    pictures: List[FramilyPictureInfo] = Field(default_factory=list)
    settings: FramilySettingsInfo
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None


class FramilyDeleteRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class MessageResponse(BaseModel):
    message: str
