from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from api.v1.auth import get_current_user
from models import User, Membership

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


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
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    if display_name is not None:
        current_user.display_name = display_name
    if email is not None:
        current_user.email = email

    db.commit()
    db.refresh(current_user)

    return {
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "display_name": current_user.display_name
        }
    }
