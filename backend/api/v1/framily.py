from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import string

from core.database import get_db
from api.v1.auth import get_current_user
from models import User, Framily, FramilySettings, Membership
from schemas.framily import (
    FramilyCheckRequest, FramilyCheckResponse, FramilyCreateRequest, FramilyConnectRequest, FramilyInviteRequest, FramilyJoinRequest,
    FramilyLeaveRequest, FramilyKickRequest, FramilyPictureInfo, FramilyPromoteRequest, FramilySettingsUpdate,
    FramilyDeleteRequest, FramilyCreateResponse, FramilyInfo, FramilyInfoResponse, FramilyUserInfo,
    SettingsInfo, MessageResponse
)

router = APIRouter(
    prefix="/framily",
    tags=["framily"],
)


def generate_framily_code() -> str:
    """Generate a unique 8-character framily code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


def generate_frame_token() -> str:
    """Generate a 64-character secure token for the frame."""
    return secrets.token_urlsafe(48)[:64]


def get_membership(db: Session, user_id: int, framily_id: int) -> Optional[Membership]:
    """Get membership for a user in a framily."""
    return db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.framily_id == framily_id
    ).first()


def is_admin(membership: Optional[Membership]) -> bool:
    """Check if membership is admin role."""
    return membership is not None and membership.role == 2


def is_member(membership: Optional[Membership]) -> bool:
    """Check if membership is member or admin role."""
    return membership is not None and membership.role >= 1


@router.post("/create", response_model=FramilyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_framily(request: FramilyCreateRequest, db: Session = Depends(get_db)):
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
        frame_token=frame_token
    )
    db.add(framily)
    db.commit()
    db.refresh(framily)

    # Create default settings
    settings = FramilySettings(
        framily_id=framily.id,
        picture_duration=10,
        shuffle_mode="random",
        transition_effect="fade",
        overlays=[]
    )
    db.add(settings)
    db.commit()

    return FramilyCreateResponse(framily_code=code, frame_token=frame_token)


@router.post("/connect", response_model=MessageResponse)
def connect_framily(
    request: FramilyConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect first user to a framily. Makes them admin."""
    framily_code = request.framily_code.strip().upper()
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )

    # Check if framily already has members
    existing_members = db.query(Membership).filter(
        Membership.framily_id == framily.id,
        Membership.role >= 1  # Active members only
    ).count()

    if existing_members > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Framily already has members. You must be invited."
        )

    # Check if user already connected
    existing_membership = get_membership(db, current_user.id, framily.id)
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already connected to this framily"
        )

    # Create membership as admin
    membership = Membership(
        user_id=current_user.id,
        framily_id=framily.id,
        role=2  # Admin
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return MessageResponse(message="Connected to framily as admin")


@router.post("/invite", response_model=MessageResponse)
def invite_user(
    request: FramilyInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to the framily. Admin only."""
    framily_code = request.framily_code.strip().upper()
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )

    # Check admin permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    # Find user to invite
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user already has membership
    existing = get_membership(db, target_user.id, framily.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already invited or member"
        )

    # Create invitation (role=0)
    invitation = Membership(
        user_id=target_user.id,
        framily_id=framily.id,
        role=0  # Invited
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return MessageResponse(message="Invitation sent")


@router.post("/join", response_model=MessageResponse)
def join_framily(
    request: FramilyJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept or decline an invitation."""
    framily_code = request.framily_code.strip().upper()
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )

    # Check for pending invitation
    membership = get_membership(db, current_user.id, framily.id)
    if not membership or membership.role != 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending invitation found"
        )

    if request.accepted:
        membership.role = 1  # Member
        db.commit()
        db.refresh(membership)
        return MessageResponse(message="Invitation accepted")
    else:
        db.delete(membership)
        db.commit()
        return MessageResponse(message="Invitation declined")


@router.post("/leave", response_model=MessageResponse)
def leave_framily(
    request: FramilyLeaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a framily."""
    framily = db.query(Framily).filter(Framily.code == request.framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )

    membership = get_membership(db, current_user.id, framily.id)
    if not membership or membership.role < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a member of this framily"
        )

    # Check if last admin trying to leave
    if membership.role == 2:
        admin_count = db.query(Membership).filter(
            Membership.framily_id == framily.id,
            Membership.role == 2
        ).count()

        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot leave as last admin. Promote another member first. Or delete the framily if you want to disband."
            )

    # Delete membership
    db.delete(membership)
    db.commit()

    return MessageResponse(message="Left framily")


@router.post("/kick", response_model=MessageResponse)
def kick_user(
    request: FramilyKickRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kick a user from the framily. Admin only."""
    framily = db.query(Framily).filter(Framily.code == request.framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found."
        )

    # Check admin permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required."
        )

    # Find user to kick
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Kicking self is just leaving
    if target_user.id == current_user.id:
        leave_framily(FramilyLeaveRequest(framily_code=request.framily_code), current_user, db)
        return MessageResponse(message="You have left the framily.")

    # Find target's membership
    target_membership = get_membership(db, target_user.id, framily.id)
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member."
        )

    db.delete(target_membership)
    db.commit()

    return MessageResponse(message="User kicked")


@router.post("/promote", response_model=MessageResponse)
def promote_user(
    request: FramilyPromoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user role. Admin only."""
    framily = db.query(Framily).filter(Framily.code == request.framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found."
        )

    # Check admin permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required."
        )

    # Find user to promote
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    target_membership = get_membership(db, target_user.id, framily.id)
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member."
        )

    # Check if demoting last admin
    if target_membership.role == 2 and request.new_role < 2:
        admin_count = db.query(Membership).filter(
            Membership.framily_id == framily.id,
            Membership.role == 2
        ).count()

        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot demote last admin. Promote another member first. Or delete the framily if you want to disband."
            )

    target_membership.role = request.new_role
    db.commit()
    db.refresh(target_membership)

    return MessageResponse(message="User role updated")


@router.post("/settings", response_model=MessageResponse)
def update_settings(
    request: FramilySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update framily settings. Admin only."""
    framily = db.query(Framily).filter(Framily.code == request.framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )

    # Check admin permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    settings = db.query(FramilySettings).filter(
        FramilySettings.framily_id == framily.id
    ).first()

    if not settings:
        # Create settings if missing
        settings = FramilySettings(framily_id=framily.id)
        db.add(settings)

    # Update settings
    if request.settings.picture_duration is not None:
        settings.picture_duration = request.settings.picture_duration
    if request.settings.shuffle_mode is not None:
        settings.shuffle_mode = request.settings.shuffle_mode
    if request.settings.transition_effect is not None:
        settings.transition_effect = request.settings.transition_effect
    if request.settings.overlays is not None:
        settings.overlays = [o.model_dump() for o in request.settings.overlays]

    db.commit()
    db.refresh(settings)

    return MessageResponse(message="Settings updated")


@router.post("/check", response_model=FramilyCheckResponse)
def check_framily(
    request: FramilyCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if framily code and frame token are valid. Used by frame device."""
    framily_code = request.framily_code
    frame_token = request.frame_token

    framily = db.query(Framily).filter(Framily.code == framily_code and Framily.frame_token == frame_token).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found"
        )

    members = db.query(User).join(Membership).filter(
        Membership.framily_id == framily.id,
        Membership.role >= 1
    ).all()

    initiated = len(members) > 0
    return FramilyCheckResponse(initiated=initiated)


@router.get("/info", response_model=FramilyInfoResponse)
def get_framily_info(
    framily_code: str = Query(..., min_length=8, max_length=8),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get framily info. Response varies by role."""
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found."
        )

    # Check membership
    membership = get_membership(db, current_user.id, framily.id)
    if not is_member(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this framily."
        )

    # Build members list
    members = []
    for m in framily.memberships:
        members.append(FramilyUserInfo(
            username=m.user.username,
            display_name=m.user.display_name,
            role=m.role,
        ))

    # Build pictures list
    pictures = []
    for v in framily.picture_visibility:
        pictures.append(FramilyPictureInfo(
            id=v.picture.id,
            uploader_username=v.picture.uploader.username
        ))

    return FramilyInfoResponse(
        code=framily.code,
        name=framily.name,
        members=members,
        pictures=pictures,
    )


@router.post("/delete", response_model=MessageResponse)
def delete_framily(
    request: FramilyDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a framily. Admin only."""
    framily = db.query(Framily).filter(Framily.code == request.framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found."
        )

    # Check admin permission
    membership = get_membership(db, current_user.id, framily.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required."
        )

    db.delete(framily)
    db.commit()

    return MessageResponse(message="Framily deleted.")
