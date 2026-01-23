from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from core.database import get_db
from core.config import settings
from core.minio import minio_client
from api.v1.auth import get_current_user
from models import User
from schemas.user import ProfileUpdate

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


ALLOWED_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for profile pictures


@router.get("/info")
def get_user_info(
    username: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user info. Response varies based on relationship."""
    target_user = db.query(User).filter(User.username == username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if requesting own info
    is_self = current_user.id == target_user.id

    if is_self:
        # Full info for self
        return {
            "user": {
                "username": target_user.username,
                "email": target_user.email,
                "display_name": target_user.display_name,
                "created_at": target_user.created_at.isoformat() if target_user.created_at else None,
            }
        }

    # Get all framilies current user is in
    current_user_framilies = {m.framily_id for m in current_user.memberships if m.role >= 1}

    # Check if target user shares any framily
    is_framily_member = False
    for m in target_user.memberships:
        if m.framily_id in current_user_framilies and m.role >= 1:
            is_framily_member = True
            break

    if is_framily_member:
        # Partial info for framily members
        return {
            "user": {
                "username": target_user.username,
                "email": target_user.email,
                "display_name": target_user.display_name,
            }
        }
    else:
        # Basic info for external users
        return {
            "user": {
                "username": target_user.username,
                "display_name": target_user.display_name,
            }
        }


@router.put("/profile")
def update_profile(
    profile: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    if profile.display_name is not None:
        current_user.display_name = profile.display_name
    if profile.email is not None:
        current_user.email = profile.email

    db.commit()
    db.refresh(current_user)

    return {
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "display_name": current_user.display_name
        }
    }


@router.post("/profile-picture")
async def post_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a profile picture for the current user."""
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
    extension = file.content_type.split("/")[-1]
    if extension == "jpeg":
        extension = "jpg"
    filename = f"profile_pictures/{current_user.username}.{extension}"

    # Delete old profile picture if exists
    for ext in ["jpg", "png", "webp", "gif"]:
        old_filename = f"profile_pictures/{current_user.username}.{ext}"
        minio_client.remove_object(settings.MINIO_BUCKET, old_filename)

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

    # Update user record
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile picture uploaded",
    }


@router.get("/profile-picture")
def get_profile_picture(
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    """Serve a profile picture. Public endpoint - no auth required."""
    # Verify the picture_id belongs to a user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found"
        )

    # Try to find the file with different extensions
    for extension in ["jpg", "png", "webp", "gif"]:
        object_name = f"profile_pictures/{user.username}.{extension}"
        try:
            response = minio_client.get_object(settings.MINIO_BUCKET, object_name)

            content_type_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
                "gif": "image/gif"
            }
            content_type = content_type_map.get(extension, "image/jpeg")

            return StreamingResponse(
                response.stream(32*1024),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                    "Content-Disposition": f"inline; filename={user.username}.{extension}"
                }
            )
        except Exception:
            continue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Profile picture file not found"
    )


@router.delete("/profile-picture")
def delete_profile_picture(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user's profile picture."""
    # Delete from MinIO
    for ext in ["jpg", "png", "webp", "gif"]:
        old_filename = f"profile_pictures/{current_user.username}.{ext}"
        minio_client.remove_object(settings.MINIO_BUCKET, old_filename)

    # Update user record
    db.commit()
    db.refresh(current_user)

    return {"message": "Profile picture deleted"}
