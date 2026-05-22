from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PictureUploadRequest(BaseModel):
    framily_codes: list[str]





class PictureMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    file_size: Optional[int] = None
    original_filename: Optional[str] = None


class PictureFramilyInfo(BaseModel):
    code: str
    name: Optional[str] = None


class PictureInfo(BaseModel):
    id: str
    framilies: list[PictureFramilyInfo]
    uploader_username: str
    uploader_display_name: Optional[str] = None
    upload_date: datetime
    metadata: Optional[PictureMetadata] = None

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


class FramilyCheck(BaseModel):
    framily_code: str = Field(..., min_length=8, max_length=8)
    frame_token: str = Field(..., min_length=64, max_length=64)
