from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from schemas.picture import PictureMetadata


class FramilyCreateRequest(BaseModel):
    name: Optional[str] = None


class FramilyCreateResponse(BaseModel):
    framily_code: str
    frame_token: str


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


class FramilyCheckResponse(BaseModel):
    initiated: bool


class FramilyDeleteRequest(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class MessageResponse(BaseModel):
    message: str

#############
# Down there is trash, not really implemented yet, just a sketch from copilot
#############

class OverlayConfig(BaseModel):
    type: str
    position: str


class FramilySettingsUpdate(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    settings: "SettingsData"


class SettingsData(BaseModel):
    picture_duration: Optional[int] = None
    shuffle_mode: Optional[str] = None
    transition_effect: Optional[str] = None
    overlays: Optional[List[OverlayConfig]] = None


class SettingsInfo(BaseModel):
    picture_duration: int
    shuffle_mode: str
    transition_effect: str
    overlays: List[OverlayConfig] = []

    class Config:
        from_attributes = True



# Update forward references
FramilySettingsUpdate.model_rebuild()
