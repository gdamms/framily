from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import verify_password, hash_password
from core.avatars import delete_avatar, USER_AVATAR_PREFIX
from api.v1.auth import get_current_user
from models import User, Framily, Picture, Membership, PictureVisibility
from schemas.user import (
    ProfileUpdate,
    UserInfo,
    UserInfoResponse,
    UserFramilyInfo,
    DeleteAccountRequest,
    ChangePasswordRequest,
)
from schemas.framily import MessageResponse

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


def build_picture_info(picture: Picture) -> dict:
    framilies = []
    for visibility in picture.visibility_records:
        framily = visibility.framily
        if framily:
            framilies.append({
                "code": framily.code,
                "name": framily.name,
            })

    return {
        "id": picture.id,
        "framilies": framilies,
        "uploader_username": picture.uploader.username if picture.uploader else "unknown",
        "uploader_display_name": picture.uploader.display_name if picture.uploader else None,
        "upload_date": picture.upload_date,
        "metadata": picture.metadata_ or {},
        "description": picture.description,
    }


def build_user_info(target_user: User, current_user: User, db: Session) -> UserInfo:
    """Build user info. Self sees everything (incl. pending invites); anyone
    else sees only the framilies/pictures they have in common with the target."""
    is_self = current_user.id == target_user.id

    current_user_framily_ids = {
        m.framily_id for m in db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.role.in_(["member", "admin"]),
        ).all()
    }

    role_filter = [Membership.user_id == target_user.id]
    if not is_self:
        role_filter.append(Membership.role.in_(["member", "admin"]))
    target_memberships = db.query(Membership).filter(*role_filter).all()

    framilies = []
    common_framily_ids = set()
    for membership in target_memberships:
        framily = membership.framily
        if not is_self and framily.id not in current_user_framily_ids:
            continue
        common_framily_ids.add(framily.id)
        framilies.append(UserFramilyInfo(
            code=framily.code,
            name=framily.name,
            role=membership.role,
            member_count=db.query(Membership).filter(
                Membership.framily_id == framily.id,
                Membership.role.in_(["member", "admin"]),
            ).count(),
            picture_count=db.query(PictureVisibility).filter(
                PictureVisibility.framily_id == framily.id,
            ).count(),
            created_at=framily.created_at,
        ))

    pictures = []
    if is_self or common_framily_ids:
        target_pictures = db.query(Picture).filter(Picture.uploaded_by == target_user.id).all()
        for picture in target_pictures:
            if is_self or set(picture.framily_ids).intersection(common_framily_ids):
                pictures.append(build_picture_info(picture))

        pictures.sort(key=lambda item: item["upload_date"], reverse=True)

    return UserInfo(
        username=target_user.username,
        email=target_user.email if is_self else None,
        display_name=target_user.display_name,
        created_at=target_user.created_at if is_self else None,
        framilies=framilies,
        pictures=pictures,
    )


@router.get("/info", response_model=UserInfoResponse)
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

    return UserInfoResponse(user=build_user_info(target_user, current_user, db))


@router.put("/profile", response_model=UserInfoResponse)
def update_profile(
    profile: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    if profile.display_name is not None:
        current_user.display_name = profile.display_name
    if profile.email is not None:
        # Check email uniqueness
        existing = db.query(User).filter(
            User.email == profile.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            )
        current_user.email = profile.email

    db.commit()
    db.refresh(current_user)

    return UserInfoResponse(user=build_user_info(current_user, current_user, db))


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change the current user's password. Requires re-entering the current password."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    current_user.hashed_password = hash_password(request.new_password)
    db.commit()

    return MessageResponse(message="Password changed")


@router.post("/delete", response_model=MessageResponse)
def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently delete the current user's account. Requires re-entering
    the password. Blocked if the user is the sole admin of any framily -
    they must promote another admin or delete the framily first, same as
    leaving a framily."""
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    admin_memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.role == "admin"
    ).all()

    sole_admin_of = []
    for membership in admin_memberships:
        admin_count = db.query(Membership).filter(
            Membership.framily_id == membership.framily_id,
            Membership.role == "admin"
        ).count()
        if admin_count == 1:
            sole_admin_of.append(membership.framily.name or membership.framily.code)

    if sole_admin_of:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You're the last admin of: " + ", ".join(sole_admin_of)
                + ". Promote another member first, or delete those framilies if you want to disband them."
            )
        )

    delete_avatar(USER_AVATAR_PREFIX, current_user.username)

    db.delete(current_user)
    db.commit()

    return MessageResponse(message="Account deleted")
