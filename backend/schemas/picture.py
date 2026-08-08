from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

CAPTION_MAX_LENGTH = 300


class PictureMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    file_size: Optional[int] = None
    original_filename: Optional[str] = None


class PictureFramilyInfo(BaseModel):
    code: str
    name: Optional[str] = None


class FocusArea(BaseModel):
    """A rectangle within the picture, normalized to fractions (0-1) of its
    own width/height. Used to bias server-side cropping when the frame's
    aspect ratio doesn't match the picture's - see api/v1/frame.py."""
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)


class PictureInfo(BaseModel):
    id: str
    framilies: list[PictureFramilyInfo]
    uploader_username: str
    uploader_display_name: Optional[str] = None
    upload_date: datetime
    metadata: Optional[PictureMetadata] = None
    description: Optional[str] = None
    focus_area: Optional[FocusArea] = None

    class Config:
        from_attributes = True


class PictureUploadResponse(BaseModel):
    picture: PictureInfo


class PictureMutationResponse(BaseModel):
    message: str
    picture: PictureInfo
    warning: Optional[str] = None


class PictureFetchResponse(BaseModel):
    metadata: dict


class PictureListResponse(BaseModel):
    pictures: list[PictureInfo]


class MessageResponse(BaseModel):
    message: str


class AddVisibilityRequest(BaseModel):
    picture_id: str
    framily_codes: list[str]


class RemoveVisibilityRequest(BaseModel):
    picture_id: str
    framily_codes: list[str]


class UpdateDescriptionRequest(BaseModel):
    picture_id: str
    # Empty string clears the caption; stored as NULL server-side either way.
    description: str = Field(default="", max_length=CAPTION_MAX_LENGTH)


class UpdateFocusAreaRequest(BaseModel):
    picture_id: str
    # None clears the focus area, falling back to a plain center crop.
    focus_area: Optional[FocusArea] = None
