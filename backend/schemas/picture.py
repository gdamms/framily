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
    framily_id: int
    url: str
    uploaded_by: Optional[int] = None
    upload_date: datetime
    metadata: Optional[PictureMetadata] = None

    class Config:
        from_attributes = True


class PictureUploadResponse(BaseModel):
    picture: PictureInfo


class PictureFetchResponse(BaseModel):
    url: str
    metadata: dict


class PictureListResponse(BaseModel):
    pictures: list[PictureInfo]


class MessageResponse(BaseModel):
    message: str
