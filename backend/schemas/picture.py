from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PictureMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    file_size: Optional[int] = None


class PictureInfo(BaseModel):
    id: str
    framily_ids: list[int]
    framily_codes: list[str]
    uploader_username: str
    uploader_display_name: str
    upload_date: datetime
    metadata: Optional[PictureMetadata] = None

    class Config:
        from_attributes = True


class PictureUploadResponse(BaseModel):
    picture: PictureInfo


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
