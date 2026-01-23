from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Request schemas
class FramilyCreate(BaseModel):
    name: Optional[str] = None


class FramilyConnect(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class FramilyInvite(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    username: str


class FramilyJoin(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    accepted: bool


class FramilyLeave(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


class FramilyKick(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    username: str


class FramilyPromote(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    username: str
    new_role: int = Field(..., ge=0, le=2)


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


class FramilyDelete(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)


# Response schemas
class FramilyCreateResponse(BaseModel):
    framily_code: str
    frame_token: str


class MemberInfo(BaseModel):
    username: str
    display_name: Optional[str] = None
    role: int
    joined_date: datetime

    class Config:
        from_attributes = True


class SettingsInfo(BaseModel):
    picture_duration: int
    shuffle_mode: str
    transition_effect: str
    overlays: List[OverlayConfig] = []

    class Config:
        from_attributes = True


class FramilyInfo(BaseModel):
    code: str
    name: Optional[str]
    created_at: datetime
    settings: Optional[SettingsInfo] = None
    members: Optional[List[MemberInfo]] = None
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class FramilyInfoResponse(BaseModel):
    framily: FramilyInfo


class MessageResponse(BaseModel):
    message: str


# Update forward references
FramilySettingsUpdate.model_rebuild()
