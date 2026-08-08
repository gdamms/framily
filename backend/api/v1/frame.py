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


def _draw_corner_text(image: Image.Image, text: str, corner: str, bottom_margin: int = 0) -> Image.Image:
    """Burn text into a corner of the image ("bottom-right" or "bottom-left").

    `bottom_margin` shifts the text up from the bottom edge - used to keep it
    clear of the caption bar (see draw_caption) when one is also being drawn.
    """
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    font_size = max(12, round(min(image.size) * 0.03))
    font = ImageFont.load_default(size=font_size)

    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = round(font_size * 0.5)
    y = image.height - text_h - margin - bbox[1] - bottom_margin
    if corner == "bottom-left":
        x = margin - bbox[0]
    else:
        x = image.width - text_w - margin - bbox[0]

    draw.text(
        (x, y), text, font=font,
        fill="white", stroke_width=max(1, font_size // 12), stroke_fill="black"
    )
    return image


def draw_uploader_credit(image: Image.Image, uploader_name: str, bottom_margin: int = 0) -> Image.Image:
    """Burn a credit into the bottom-right corner of the image."""
    return _draw_corner_text(image, uploader_name, "bottom-right", bottom_margin)


def draw_date(image: Image.Image, upload_date: datetime, bottom_margin: int = 0) -> Image.Image:
    """Burn the picture's upload date into the bottom-left corner of the image."""
    text = upload_date.strftime("%d/%m/%Y")
    return _draw_corner_text(image, text, "bottom-left", bottom_margin)


def draw_caption(image: Image.Image, caption: str) -> tuple[Image.Image, int]:
    """Burn a picture's caption into a semi-transparent bar across the bottom
    of the image, wrapped to fit its width. Returns the resulting image and
    the bar's height in pixels, so the uploader-credit/date corner overlays
    can be shifted above it instead of overlapping the caption text."""
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    font_size = max(14, round(min(image.size) * 0.035))
    font = ImageFont.load_default(size=font_size)
    padding = round(font_size * 0.6)
    max_width = image.width - 2 * padding

    measure = ImageDraw.Draw(image)
    words = caption.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or measure.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_height = font.getbbox("Ag")[3] + round(font_size * 0.25)
    bar_height = line_height * len(lines) + padding * 2

    bar = Image.new("RGBA", image.size, (0, 0, 0, 0))
    bar_draw = ImageDraw.Draw(bar)
    bar_draw.rectangle(
        [(0, image.height - bar_height), (image.width, image.height)],
        fill=(0, 0, 0, 140),
    )

    y = image.height - bar_height + padding
    for line in lines:
        bbox = bar_draw.textbbox((0, 0), line, font=font)
        x = (image.width - (bbox[2] - bbox[0])) / 2 - bbox[0]
        bar_draw.text((x, y), line, font=font, fill="white")
        y += line_height

    return Image.alpha_composite(image, bar), bar_height


def _resize_crop_centered(image: Image.Image, crop_w: int, crop_h: int) -> Image.Image:
    """Scale the image up to the smallest size that covers (crop_w, crop_h),
    then center-crop the rest away. Used when a picture has no focus area -
    this is the original, unbiased crop behavior."""
    img_w, img_h = image.size
    scale = max(crop_w / img_w, crop_h / img_h)
    new_w, new_h = round(img_w * scale), round(img_h * scale)
    image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    left = (new_w - crop_w) // 2
    top = (new_h - crop_h) // 2
    return image.crop((left, top, left + crop_w, top + crop_h))


def _resize_crop_to_focus(image: Image.Image, crop_w: int, crop_h: int, focus_area: dict) -> Image.Image:
    """Crop to a (crop_w, crop_h)-shaped box that always fully contains the
    focus area, hugging it as tightly as possible (i.e. zooming in on it)
    rather than showing extra surrounding picture. If the focus area's own
    shape can't fit inside the picture at the target aspect ratio, the box
    is allowed to extend past the picture's edges - those parts are filled
    with black bars rather than cutting into the focus area - but only by
    as much as is unavoidable: a bar is only ever added where the picture
    itself has run out, never in place of picture content that could
    otherwise have been shown."""
    img_w, img_h = image.size
    fx0 = focus_area["x"] * img_w
    fy0 = focus_area["y"] * img_h
    fw = focus_area["width"] * img_w
    fh = focus_area["height"] * img_h
    fx1, fy1 = fx0 + fw, fy0 + fh

    target_ar = crop_w / crop_h

    # Smallest box (at the target aspect ratio) that contains the focus
    # rect - the tightest possible crop around it. This is >= the largest
    # box that fits entirely inside the picture exactly when bars are
    # unavoidable (the focus area's own shape doesn't fit the target aspect
    # ratio within the picture's bounds); the position clamp below then
    # pushes the box against the picture's edges wherever it has room to,
    # so bars only ever appear where the picture has genuinely run out.
    bw = max(fw, fh * target_ar)
    bh = bw / target_ar

    # Center the box on the focus area, then nudge it back so it still fully
    # contains the focus rect (and, when it's small enough to fit, back
    # inside the picture's bounds too).
    bx0 = fx0 + fw / 2 - bw / 2
    by0 = fy0 + fh / 2 - bh / 2
    bx0 = min(max(bx0, fx1 - bw), fx0)
    by0 = min(max(by0, fy1 - bh), fy0)
    if bw <= img_w:
        bx0 = min(max(bx0, 0), img_w - bw)
    if bh <= img_h:
        by0 = min(max(by0, 0), img_h - bh)

    bx0, by0 = round(bx0), round(by0)
    bw_i, bh_i = max(round(bw), 1), max(round(bh), 1)

    # Portion of the box that actually overlaps the picture; anything outside
    # of that stays black.
    ox0, oy0 = max(bx0, 0), max(by0, 0)
    ox1, oy1 = min(bx0 + bw_i, img_w), min(by0 + bh_i, img_h)

    fill = (0, 0, 0, 255) if image.mode == "RGBA" else "black"
    canvas = Image.new(image.mode, (bw_i, bh_i), fill)
    if ox0 < ox1 and oy0 < oy1:
        region = image.crop((ox0, oy0, ox1, oy1))
        canvas.paste(region, (ox0 - bx0, oy0 - by0))

    return canvas.resize((crop_w, crop_h), Image.Resampling.LANCZOS)


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
    # Caption is only ever drawn if the picture actually has one set - an
    # enabled setting with no caption on the picture draws nothing.
    caption = (picture.description or "").strip() if framily.settings and framily.settings.show_caption else ""
    needs_caption = bool(caption)
    # Adaptive contrast/saturation/gamma correction tuned for the panel's
    # 6-color gamut (see core/image_preprocess.py); like the overlays above,
    # this is applied here rather than on the frame and isn't exposed via
    # /frame/settings.
    preprocess_level = framily.settings.preprocess_level if framily.settings else 0
    needs_preprocess = bool(preprocess_level)

    if (
        not needs_rotation and not needs_resize and not needs_credit
        and not needs_date and not needs_preprocess and not needs_caption
    ):
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

        if picture.focus_area:
            image = _resize_crop_to_focus(image, crop_w, crop_h, picture.focus_area)
        else:
            image = _resize_crop_centered(image, crop_w, crop_h)

    if needs_preprocess:
        # Run on the final (already resized/cropped) pixels so the adaptive
        # statistics reflect exactly what the panel will render, and before
        # the overlays below so their fixed white/black styling isn't
        # affected by the contrast/saturation correction.
        image = preprocess_for_eink(image, preprocess_level)

    # Draw the caption first so its bar height can push the corner overlays
    # up above it instead of overlapping the caption text.
    caption_bar_height = 0
    if needs_caption:
        image, caption_bar_height = draw_caption(image, caption)

    if needs_credit:
        image = draw_uploader_credit(image, uploader_name, bottom_margin=caption_bar_height)

    if needs_date:
        image = draw_date(image, picture.upload_date, bottom_margin=caption_bar_height)

    if needs_rotation:
        image = image.rotate(int(orientation), expand=True)

    pil_format = "JPEG" if file_format.lower() in ("jpg", "jpeg") else file_format.upper()
    if pil_format == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    output = BytesIO()
    image.save(output, format=pil_format)

    return Response(content=output.getvalue(), media_type=media_type, headers=headers)
