from pydantic import BaseModel, Field
from typing import Optional


class FrameAuthRequest(BaseModel):
    """Body shared by all frame-device endpoints that authenticate via
    framily_code + frame_token instead of a user JWT."""
    framily_code: str = Field(..., min_length=8, max_length=8)
    frame_token: str = Field(..., min_length=64, max_length=64)


class FrameCreateRequest(BaseModel):
    name: Optional[str] = None


class FrameCreateResponse(BaseModel):
    framily_code: str
    frame_token: str


class FrameCheckResponse(BaseModel):
    initiated: bool


class FrameStatusRequest(FrameAuthRequest):
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None


class FrameSettingsResponse(BaseModel):
    interval_minutes: int
