from pydantic import BaseModel, Field
from typing import Literal, Optional, List

Orientation = Literal["0", "90", "180", "270"]


class FramilyCreateRequest(BaseModel):
    name: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None


class FramilyCreateResponse(BaseModel):
    framily_code: str
    frame_token: str


class FramilySettingsInfo(BaseModel):
    orientation: Orientation
    interval_minutes: int


class FramilyUpdateSettingsRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    orientation: Optional[Orientation] = None
    interval_minutes: Optional[int] = Field(default=None, ge=1, le=1440)


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


class FramilyCheckRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    frame_token: str = Field(..., min_length=64, max_length=64)


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


class FramilyCheckResponse(BaseModel):
    initiated: bool


class FramilyDeleteRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class MessageResponse(BaseModel):
    message: str
