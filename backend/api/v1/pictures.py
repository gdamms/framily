from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import uuid
from io import BytesIO

from core.database import get_db
from core.config import settings
from core.minio import minio_client
from api.v1.auth import get_current_user
from api.v1.framily import get_membership, is_member, is_admin
from models import User, Framily, Picture

router = APIRouter(
    prefix="/pictures",
    tags=["pictures"],
)

ALLOWED_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_picture(
    framily_code: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a picture to a framily."""
    # Verify framily exists
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )
    
    # Check member permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_member(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a member to upload pictures"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_FORMATS)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique ID and filename
    picture_id = str(uuid.uuid4())
    extension = file.content_type.split("/")[-1]
    if extension == "jpeg":
        extension = "jpg"
    filename = f"{framily.code}/{picture_id}.{extension}"
    
    # Upload to MinIO
    try:
        minio_client.put_object(
            settings.MINIO_BUCKET,
            filename,
            BytesIO(content),
            len(content),
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Build URL
    url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{filename}"
    
    # Create picture record
    picture = Picture(
        id=picture_id,
        framily_id=framily.id,
        uploaded_by=current_user.id,
        url=url,
        metadata_={
            "format": extension,
            "file_size": len(content),
            "original_filename": file.filename
        }
    )
    db.add(picture)
    db.commit()
    db.refresh(picture)
    
    return {
        "picture": {
            "id": picture.id,
            "framily_id": picture.framily_id,
            "url": picture.url,
            "uploaded_by": picture.uploaded_by,
            "upload_date": picture.upload_date.isoformat(),
            "metadata": picture.metadata_
        }
    }


@router.get("/fetch")
def fetch_picture(
    authorization: str = Header(..., alias="X-Frame-Token"),
    db: Session = Depends(get_db)
):
    """Fetch a random picture for the frame. Uses frame token auth."""
    # Find framily by frame token
    framily = db.query(Framily).filter(Framily.frame_token == authorization).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid frame token"
        )
    
    # Get a random picture
    picture = db.query(Picture).filter(
        Picture.framily_id == framily.id
    ).order_by(func.random()).first()
    
    if not picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pictures available"
        )
    
    # Get uploader info
    uploader_name = None
    if picture.uploader:
        uploader_name = picture.uploader.display_name or picture.uploader.username
    
    return {
        "url": picture.url,
        "metadata": {
            "uploaded_by": uploader_name,
            "upload_date": picture.upload_date.isoformat()
        }
    }


@router.get("/list")
def list_pictures(
    framily_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all pictures in a framily."""
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )
    
    # Check member permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_member(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a member to view pictures"
        )
    
    pictures = db.query(Picture).filter(
        Picture.framily_id == framily.id
    ).order_by(Picture.upload_date.desc()).all()
    
    return {
        "pictures": [
            {
                "id": p.id,
                "framily_id": p.framily_id,
                "url": p.url,
                "uploaded_by": p.uploaded_by,
                "uploader_name": p.uploader.display_name or p.uploader.username if p.uploader else None,
                "upload_date": p.upload_date.isoformat(),
                "metadata": p.metadata_
            }
            for p in pictures
        ]
    }


@router.delete("/{picture_id}")
def delete_picture(
    picture_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a picture. Own picture or admin only."""
    picture = db.query(Picture).filter(Picture.id == picture_id).first()
    if not picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Picture not found"
        )
    
    # Check permissions
    membership = get_membership(db, current_user.id, picture.framily_id)
    
    # Must be member
    if not is_member(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this framily"
        )
    
    # Must be uploader or admin
    is_uploader = picture.uploaded_by == current_user.id
    if not is_uploader and not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete own pictures or be admin"
        )
    
    # Delete from MinIO
    try:
        # Extract object name from URL
        url_path = picture.url.split(f"/{settings.MINIO_BUCKET}/")[-1]
        minio_client.remove_object(settings.MINIO_BUCKET, url_path)
    except Exception:
        pass  # Continue even if MinIO delete fails
    
    # Delete from database
    db.delete(picture)
    db.commit()
    
    return {"message": "Picture deleted"}
