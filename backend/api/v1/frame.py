from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import secrets
import string

from core.database import get_db
from core.config import settings
from core.minio import s3_client
from core.image_preprocess import preprocess_for_eink
from core.avatars import delete_avatar, FRAMILY_AVATAR_PREFIX
from models import User, Framily, FramilySettings, Membership, PictureVisibility
from schemas.framily import MessageResponse
from schemas.frame import (
    FrameAuthRequest, FrameCreateRequest, FrameCreateResponse,
    FrameCheckResponse, FrameStatusRequest, FrameSettingsResponse
)

router = APIRouter(
    prefix="/frame",
    tags=["frame"],
)


def generate_framily_code() -> str:
    """Generate a unique 8-character framily code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


def generate_frame_token() -> str:
    """Generate a 64-character secure token for the frame."""
    return secrets.token_urlsafe(48)[:64]


def _draw_corner_text(image: Image.Image, text: str, corner: str) -> Image.Image:
    """Burn text into a corner of the image ("bottom-right" or "bottom-left")."""
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    font_size = max(12, round(min(image.size) * 0.03))
    font = ImageFont.load_default(size=font_size)

    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = round(font_size * 0.5)
    y = image.height - text_h - margin - bbox[1]
    if corner == "bottom-left":
        x = margin - bbox[0]
    else:
        x = image.width - text_w - margin - bbox[0]

    draw.text(
        (x, y), text, font=font,
        fill="white", stroke_width=max(1, font_size // 12), stroke_fill="black"
    )
    return image


def draw_uploader_credit(image: Image.Image, uploader_name: str) -> Image.Image:
    """Burn a credit into the bottom-right corner of the image."""
    return _draw_corner_text(image, uploader_name, "bottom-right")


def draw_date(image: Image.Image, upload_date: datetime) -> Image.Image:
    """Burn the picture's upload date into the bottom-left corner of the image."""
    text = upload_date.strftime("%d/%m/%Y")
    return _draw_corner_text(image, text, "bottom-left")


def get_framily_by_frame_auth(db: Session, framily_code: str, frame_token: str) -> Framily:
    """Look up a framily by code + frame token. Shared auth for all frame-device endpoints."""
    framily = db.query(Framily).filter(
        Framily.code == framily_code, Framily.frame_token == frame_token
    ).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found or invalid frame token"
        )
    return framily


@router.post("/create", response_model=FrameCreateResponse, status_code=status.HTTP_201_CREATED)
def create_framily(request: FrameCreateRequest, db: Session = Depends(get_db)):
    """Create a new framily. This endpoint is used by the frame device."""
    # Generate unique code
    while True:
        code = generate_framily_code()
        existing = db.query(Framily).filter(Framily.code == code).first()
        if not existing:
            break

    frame_token = generate_frame_token()

    # Create framily
    framily = Framily(
        code=code,
        name=request.name or code,
        frame_token=frame_token,
    )
    db.add(framily)
    db.commit()
    db.refresh(framily)

    # Create default settings
    framily_settings = FramilySettings(framily_id=framily.id)
    db.add(framily_settings)
    db.commit()

    return FrameCreateResponse(framily_code=code, frame_token=frame_token)


@router.post("/check", response_model=FrameCheckResponse)
def check_framily(request: FrameAuthRequest, db: Session = Depends(get_db)):
    """Check if framily code and frame token are valid, and whether a user has
    set the framily up yet. Used by the frame device."""
    framily = get_framily_by_frame_auth(db, request.framily_code, request.frame_token)

    members = db.query(User).join(Membership).filter(
        Membership.framily_id == framily.id,
        Membership.role.in_(["member", "admin"])
    ).all()

    return FrameCheckResponse(initiated=len(members) > 0)


@router.post("/delete", response_model=MessageResponse)
def delete_framily(request: FrameAuthRequest, db: Session = Depends(get_db)):
    """Delete a framily. Used by the frame device (e.g. its "Reset Framily"
    action), authenticated via frame token instead of a user JWT. Cascade
    deletes remove all memberships and picture visibilities along with it;
    uploaded pictures themselves are left intact."""
    framily = get_framily_by_frame_auth(db, request.framily_code, request.frame_token)

    delete_avatar(FRAMILY_AVATAR_PREFIX, framily.code)

    db.delete(framily)
    db.commit()

    return MessageResponse(message="Framily deleted.")


@router.post("/status", response_model=MessageResponse)
def update_status(request: FrameStatusRequest, db: Session = Depends(get_db)):
    """Report frame status information: display resolution and the frame's
    current IP address on the Wi-Fi network (so the web UI can be reached
    directly). Reported separately from /frame/create since none of this is
    known until the e-ink driver has initialized and Wi-Fi is connected, and
    the frame re-reports it on every fetch cycle since the IP can change."""
    framily = get_framily_by_frame_auth(db, request.framily_code, request.frame_token)

    if request.resolution_width is not None:
        framily.resolution_width = request.resolution_width
    if request.resolution_height is not None:
        framily.resolution_height = request.resolution_height
    if request.ip_address is not None:
        framily.ip_address = request.ip_address

    db.commit()

    return MessageResponse(message="Status updated")


@router.post("/settings", response_model=FrameSettingsResponse)
def get_frame_settings(request: FrameAuthRequest, db: Session = Depends(get_db)):
    """Fetch settings the frame device needs to operate, e.g. the delay
    between picture fetches. Used by the frame device."""
    framily = get_framily_by_frame_auth(db, request.framily_code, request.frame_token)

    interval_minutes = framily.settings.interval_minutes if framily.settings else 5
    return FrameSettingsResponse(interval_minutes=interval_minutes)


@router.post("/fetch")
def fetch_picture(request: FrameAuthRequest, db: Session = Depends(get_db)):
    """Fetch a random picture for the frame. Uses frame token auth."""
    framily = get_framily_by_frame_auth(db, request.framily_code, request.frame_token)

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
    # comes out already oriented for how the frame is physically mounted, and
    # crop/resize to exactly cover the frame's reported resolution (scale up
    # to the smallest size that covers the frame, then center-crop the rest).
    orientation = framily.settings.orientation if framily.settings else "0"
    needs_rotation = bool(orientation and orientation != "0")
    needs_resize = bool(framily.resolution_width and framily.resolution_height)
    # The uploader-credit and date overlays are burned into the image
    # server-side; they're intentionally not exposed via /frame/settings -
    # the frame device has no need to know about them.
    needs_credit = bool(framily.settings and framily.settings.show_uploader_name and uploader_name)
    needs_date = bool(framily.settings and framily.settings.show_date and picture.upload_date)
    # Adaptive contrast/saturation/gamma correction tuned for the panel's
    # 6-color gamut (see core/image_preprocess.py); like the overlays above,
    # this is applied here rather than on the frame and isn't exposed via
    # /frame/settings.
    preprocess_level = framily.settings.preprocess_level if framily.settings else 0
    needs_preprocess = bool(preprocess_level)

    if not needs_rotation and not needs_resize and not needs_credit and not needs_date and not needs_preprocess:
        return StreamingResponse(
            s3_client.get_object(settings.S3_BUCKET, object_name).stream(32 * 1024),
            media_type=media_type,
            headers=headers
        )

    raw = b"".join(s3_client.get_object(settings.S3_BUCKET, object_name).stream(32 * 1024))
    image = Image.open(BytesIO(raw))

    if needs_resize:
        target_w, target_h = framily.resolution_width, framily.resolution_height
        # The rotation below swaps width/height for a 90/270 turn, so crop to
        # the swapped dimensions here - after rotating, the image ends up
        # exactly target_w x target_h as reported by the frame.
        if needs_rotation and orientation in ("90", "270"):
            crop_w, crop_h = target_h, target_w
        else:
            crop_w, crop_h = target_w, target_h

        img_w, img_h = image.size
        scale = max(crop_w / img_w, crop_h / img_h)
        new_w, new_h = round(img_w * scale), round(img_h * scale)
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        left = (new_w - crop_w) // 2
        top = (new_h - crop_h) // 2
        image = image.crop((left, top, left + crop_w, top + crop_h))

    if needs_preprocess:
        # Run on the final (already resized/cropped) pixels so the adaptive
        # statistics reflect exactly what the panel will render, and before
        # the overlays below so their fixed white/black styling isn't
        # affected by the contrast/saturation correction.
        image = preprocess_for_eink(image, preprocess_level)

    if needs_credit:
        image = draw_uploader_credit(image, uploader_name)

    if needs_date:
        image = draw_date(image, picture.upload_date)

    if needs_rotation:
        image = image.rotate(int(orientation), expand=True)

    pil_format = "JPEG" if file_format.lower() in ("jpg", "jpeg") else file_format.upper()
    if pil_format == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    output = BytesIO()
    image.save(output, format=pil_format)

    return Response(content=output.getvalue(), media_type=media_type, headers=headers)
