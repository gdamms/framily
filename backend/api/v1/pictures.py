from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from io import BytesIO
from typing import Optional
from PIL import Image

from core.database import get_db
from core.config import settings
from core.minio import s3_client
from api.v1.auth import get_current_user
from api.v1.framily import get_membership, is_member, is_admin
from models import User, Framily, Picture, PictureVisibility, Membership
from schemas.picture import (
    AddVisibilityRequest,
    RemoveVisibilityRequest,
    FramilyCheck,
    PictureUploadResponse,
    PictureListResponse,
    PictureMutationResponse,
)

router = APIRouter(
    prefix="/pictures",
    tags=["pictures"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UNSUPPORTED_IMAGE_FORMATS = {"GIF"}  # Animated formats aren't supported by the frame display.


def get_picture_info(picture: Picture, db: Session) -> dict:
    """Helper to build picture info dict with framily information."""
    framilies = []
    for v in picture.visibility_records:
        framily = db.query(Framily).filter(Framily.id == v.framily_id).first()
        if framily:
            framilies.append({
                "code": framily.code,
                "name": framily.name
            })

    return {
        "id": picture.id,
        "framilies": framilies,
        "uploader_username": picture.uploader.username if picture.uploader else "unknown",
        "uploader_display_name": picture.uploader.display_name if picture.uploader else None,
        "upload_date": picture.upload_date,
        "metadata": picture.metadata_ or {}
    }


@router.post("/upload", response_model=PictureUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_picture(
    framily_codes: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a picture and make it visible to one or more framilies.

    framily_codes is a comma-separated list of codes (sent as a multipart form
    field alongside the file, since a JSON body can't be combined with a file
    upload in the same request).
    """
    codes = [code.strip() for code in framily_codes.split(",") if code.strip()]
    if not codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one framily_code is required."
        )

    # Verify all framilies exist and user is a member
    framilies = []
    for code in codes:
        framily = db.query(Framily).filter(Framily.code == code).first()
        if not framily:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framily not found: {code}."
            )

        membership = get_membership(db, current_user.id, framily.id)
        if not is_member(membership):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Must be a member to upload pictures to: {code}."
            )
        framilies.append(framily)

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB."
        )

    # Validate image by trying to open it with PIL. verify() invalidates the
    # Image object for further use, so read the format before calling it and
    # reopen the file afterwards for the actual conversion below.
    try:
        image = Image.open(BytesIO(content))
        image_format = (image.format or "").upper()
        image.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file."
        )

    if not image_format or image_format in UNSUPPORTED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. GIFs and videos are not supported."
        )

    # Convert image to a consistent format (PNG) for storage.
    image = Image.open(BytesIO(content))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    width, height = image.size

    output = BytesIO()
    image.save(output, format="PNG")
    content = output.getvalue()

    # Sanity check: make sure the converted bytes actually decode as a valid
    # PNG before we persist and upload them.
    try:
        Image.open(BytesIO(content)).verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert image."
        )

    # Generate unique ID and filename
    picture_id = str(uuid.uuid4())
    filename = f"shared/{picture_id}.png"

    # Upload to S3 storage
    try:
        s3_client.put_object(
            settings.S3_BUCKET,
            filename,
            BytesIO(content),
            len(content),
            content_type="image/png"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Create picture record
    picture = Picture(
        id=picture_id,
        uploaded_by=current_user.id,
        metadata_={
            "format": "png",
            "width": width,
            "height": height,
            "file_size": len(content),
            "original_filename": file.filename,
        }
    )
    db.add(picture)
    db.flush()  # Get the picture ID before adding visibility records

    # Create visibility records for each framily
    for framily in framilies:
        visibility = PictureVisibility(
            picture_id=picture_id,
            framily_id=framily.id
        )
        db.add(visibility)

    db.commit()
    db.refresh(picture)

    return {
        "picture": get_picture_info(picture, db)
    }


@router.post("/add-visibility", response_model=PictureMutationResponse, status_code=status.HTTP_200_OK)
def add_visibility(
    request: AddVisibilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add visibility to additional framilies for an existing picture."""
    # Get picture
    picture = db.query(Picture).filter(Picture.id == request.picture_id).first()
    if not picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Picture not found"
        )

    # Only uploader can add visibility
    if picture.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the uploader can add visibility to a picture"
        )

    added_framilies = []
    for code in request.framily_codes:
        framily = db.query(Framily).filter(Framily.code == code).first()
        if not framily:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framily not found: {code}."
            )

        # Check user is a member of this framily
        membership = get_membership(db, current_user.id, framily.id)
        if not is_member(membership):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Must be a member to add visibility to: {code}"
            )

        # Check if visibility already exists
        existing = db.query(PictureVisibility).filter(
            PictureVisibility.picture_id == picture.id,
            PictureVisibility.framily_id == framily.id
        ).first()

        if not existing:
            visibility = PictureVisibility(
                picture_id=picture.id,
                framily_id=framily.id
            )
            db.add(visibility)
            added_framilies.append(code)

    db.commit()
    db.refresh(picture)

    return {
        "message": f"Visibility added to framilies: {', '.join(added_framilies) if added_framilies else 'none (already visible)'}",
        "picture": get_picture_info(picture, db)
    }


@router.post("/remove-visibility", response_model=PictureMutationResponse, status_code=status.HTTP_200_OK)
def remove_visibility(
    request: RemoveVisibilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove visibility from specific framilies without deleting the picture."""
    # Get picture
    picture = db.query(Picture).filter(Picture.id == request.picture_id).first()
    if not picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Picture not found"
        )

    is_uploader = picture.uploaded_by == current_user.id

    removed_framilies = []
    for code in request.framily_codes:
        framily = db.query(Framily).filter(Framily.code == code).first()
        if not framily:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framily not found: {code}"
            )

        # Uploader can remove from any framily; a framily admin can remove
        # the picture from their own framily's view (moderation), even if
        # they didn't upload it.
        if not is_uploader:
            membership = get_membership(db, current_user.id, framily.id)
            if not is_admin(membership):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Must be the uploader or an admin of {code} to remove visibility"
                )

        # Remove visibility record if it exists
        visibility = db.query(PictureVisibility).filter(
            PictureVisibility.picture_id == picture.id,
            PictureVisibility.framily_id == framily.id
        ).first()

        if visibility:
            db.delete(visibility)
            removed_framilies.append(code)

    db.commit()
    db.refresh(picture)

    # Check if picture has no visibility left
    remaining_visibility = db.query(PictureVisibility).filter(
        PictureVisibility.picture_id == picture.id
    ).count()

    return {
        "message": f"Visibility removed from framilies: {', '.join(removed_framilies) if removed_framilies else 'none'}",
        "picture": get_picture_info(picture, db),
        "warning": "Picture has no visibility left" if remaining_visibility == 0 else None
    }


@router.post("/fetch")
def fetch_picture(
    request: FramilyCheck,
    db: Session = Depends(get_db)
):
    """Fetch a random picture for the frame. Uses frame token auth."""
    # Find framily by frame token
    framily_code = request.framily_code
    frame_token = request.frame_token

    framily = db.query(Framily).filter(
        Framily.code == framily_code, Framily.frame_token == frame_token
    ).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found or invalid frame token"
        )

    # Get a random picture visible to this framily
    visibility = db.query(PictureVisibility).filter(
        PictureVisibility.framily_id == framily.id
    ).order_by(func.random()).first()

    if not visibility:
        # No pictures available for this framily
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    picture = visibility.picture

    # Get uploader info
    uploader_name = None
    if picture.uploader:
        uploader_name = picture.uploader.display_name or picture.uploader.username

    file_format = picture.metadata_.get("format", "jpg") if picture.metadata_ else "jpg"
    object_name = f"shared/{picture.id}.{file_format}"
    media_type = f"image/{file_format}"
    headers = {
        "Cache-Control": "no-cache",
        "X-Picture-ID": picture.id,
        "X-Uploader-Name": uploader_name or "Unknown"
    }

    # The frame just displays whatever it's given as-is - rotate here so it
    # comes out already oriented for how the frame is physically mounted.
    orientation = framily.settings.orientation if framily.settings else "0"
    if orientation and orientation != "0":
        raw = b"".join(s3_client.get_object(settings.S3_BUCKET, object_name).stream(32 * 1024))
        image = Image.open(BytesIO(raw))
        image = image.rotate(int(orientation), expand=True)

        pil_format = "JPEG" if file_format.lower() in ("jpg", "jpeg") else file_format.upper()
        if pil_format == "JPEG" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        output = BytesIO()
        image.save(output, format=pil_format)

        return Response(content=output.getvalue(), media_type=media_type, headers=headers)

    return StreamingResponse(
        s3_client.get_object(settings.S3_BUCKET, object_name).stream(32 * 1024),
        media_type=media_type,
        headers=headers
    )


@router.get("/list", response_model=PictureListResponse)
def list_pictures(
    framily_code: Optional[str] = None,
    username: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List pictures. Accepts either framily_code or username (not both).
    - framily_code: list all pictures visible to that framily (user must be member).
    - username: list all pictures uploaded by that user that are visible in a
      framily shared with the current user. If the user is the current user,
      return all their pictures.
    """
    if framily_code and username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either framily_code or username, not both"
        )

    if not framily_code and not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either framily_code or username"
        )

    if framily_code:
        # List pictures for a framily
        framily = db.query(Framily).filter(Framily.code == framily_code).first()
        if not framily:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Framily not found"
            )

        membership = get_membership(db, current_user.id, framily.id)
        if not is_member(membership):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be a member to view pictures"
            )

        visibilities = db.query(PictureVisibility).filter(
            PictureVisibility.framily_id == framily.id
        ).all()

        pictures = []
        for v in visibilities:
            picture = v.picture
            if picture:
                pictures.append(get_picture_info(picture, db))

        pictures.sort(key=lambda x: x["upload_date"], reverse=True)
        return {"pictures": pictures}

    else:
        # List pictures for a user
        target_user = db.query(User).filter(User.username == username).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get current user's framily IDs
        current_user_framily_ids = {
            m.framily_id for m in db.query(Membership).filter(
                Membership.user_id == current_user.id,
                Membership.role >= 1
            ).all()
        }

        # Get all pictures uploaded by the target user
        user_pictures = db.query(Picture).filter(
            Picture.uploaded_by == target_user.id
        ).all()

        pictures = []
        for picture in user_pictures:
            picture_framily_ids = set(picture.framily_ids)
            # Show picture if current user shares a framily with the picture
            if current_user.id == target_user.id or picture_framily_ids.intersection(current_user_framily_ids):
                pictures.append(get_picture_info(picture, db))

        pictures.sort(key=lambda x: x["upload_date"], reverse=True)
        return {"pictures": pictures}


@router.get("/list-all", response_model=PictureListResponse)
def list_all_pictures(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all pictures visible to the current user across all their framilies."""
    # Get all framilies user is a member of (role >= 1)
    memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.role >= 1
    ).all()

    framily_ids = [m.framily_id for m in memberships]

    if not framily_ids:
        return {"pictures": []}

    # Get all pictures visible to any of user's framilies
    visibilities = db.query(PictureVisibility).filter(
        PictureVisibility.framily_id.in_(framily_ids)
    ).all()

    # Use dict to deduplicate by picture_id
    seen_pictures = {}
    for v in visibilities:
        picture = v.picture
        if picture and picture.id not in seen_pictures:
            seen_pictures[picture.id] = get_picture_info(picture, db)

    pictures = list(seen_pictures.values())
    # Sort by upload date descending
    pictures.sort(key=lambda x: x["upload_date"], reverse=True)

    return {"pictures": pictures}


@router.delete("/{picture_id}")
def delete_picture(
    picture_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a picture entirely, uploader only. To remove a picture from a
    single framily's view without deleting it (e.g. framily admin moderation),
    use POST /pictures/remove-visibility instead."""
    picture = db.query(Picture).filter(Picture.id == picture_id).first()
    if not picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Picture not found"
        )

    is_uploader = picture.uploaded_by == current_user.id

    if not is_uploader:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the uploader can delete a picture. Use remove-visibility to take it down from a specific framily."
        )

    # Delete from S3 storage
    try:
        file_format = picture.metadata_.get("format", "jpg") if picture.metadata_ else "jpg"
        object_name = f"shared/{picture_id}.{file_format}"
        s3_client.remove_object(settings.S3_BUCKET, object_name)
    except Exception:
        pass  # Continue even if S3 delete fails

    # Delete all visibility records (cascade will handle this, but be explicit)
    db.query(PictureVisibility).filter(
        PictureVisibility.picture_id == picture.id
    ).delete()

    # Delete picture from database
    db.delete(picture)
    db.commit()

    return {"message": "Picture deleted"}


@router.get("/{picture_id}")
def get_picture_image(
    picture_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve a picture image from S3 storage."""
    # Get picture from database
    picture = db.query(Picture).filter(Picture.id == picture_id).first()
    if not picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Picture not found"
        )

    # Check if user has access through any framily
    # Get user's framily IDs (member role >= 1)
    memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.role >= 1
    ).all()
    user_framily_ids = {m.framily_id for m in memberships}

    # Get picture's visible framily IDs
    picture_framily_ids = set(picture.framily_ids)

    # Check if there's any overlap
    if not user_framily_ids.intersection(picture_framily_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of any framily this picture is visible to"
        )

    # Determine file extension from metadata
    file_format = picture.metadata_.get("format", "jpg") if picture.metadata_ else "jpg"
    object_name = f"shared/{picture_id}.{file_format}"

    # Get object from S3 storage
    response = s3_client.get_object(settings.S3_BUCKET, object_name)

    # Determine content type
    content_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif"
    }
    content_type = content_type_map.get(file_format.lower(), "image/jpeg")

    return StreamingResponse(
        response.stream(32*1024),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
            "Content-Disposition": f"inline; filename={picture_id}.{file_format}"
        }
    )
