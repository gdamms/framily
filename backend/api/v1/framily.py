from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from api.v1.auth import get_current_user
from models import User, Framily, Membership
from schemas.framily import (
    FramilyConnectRequest, FramilyInviteRequest, FramilyJoinRequest,
    FramilyLeaveRequest, FramilyKickRequest, FramilyPictureInfo, FramilyPromoteRequest,
    FramilyDeleteRequest, FramilyInfoResponse, FramilySettingsInfo, FramilyUserInfo,
    FramilyUpdateSettingsRequest, MessageResponse
)

router = APIRouter(
    prefix="/framily",
    tags=["framily"],
)


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
        settings=FramilySettingsInfo(
            orientation=framily.settings.orientation if framily.settings else "0",
            interval_minutes=framily.settings.interval_minutes if framily.settings else 5,
            show_uploader_name=framily.settings.show_uploader_name if framily.settings else False,
        ),
        resolution_width=framily.resolution_width,
        resolution_height=framily.resolution_height,
    )


@router.put("/settings", response_model=MessageResponse)
def update_framily_settings(
    request: FramilyUpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a framily's name and/or display settings. Admin only."""
    framily_code = request.framily_code.strip().upper()
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found."
        )

    membership = get_membership(db, current_user.id, framily.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required."
        )

    if request.name is not None:
        stripped_name = request.name.strip()
        if not stripped_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Framily name cannot be empty."
            )
        framily.name = stripped_name

    if framily.settings:
        if request.orientation is not None:
            framily.settings.orientation = request.orientation
        if request.interval_minutes is not None:
            framily.settings.interval_minutes = request.interval_minutes
        if request.show_uploader_name is not None:
            framily.settings.show_uploader_name = request.show_uploader_name

    db.commit()

    return MessageResponse(message="Framily settings updated.")


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
