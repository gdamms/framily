from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from core.avatars import save_avatar, stream_avatar, delete_avatar, USER_AVATAR_PREFIX, FRAMILY_AVATAR_PREFIX
from api.v1.auth import get_current_user
from api.v1.framily import get_membership, is_admin, is_member
from models import User, Framily

router = APIRouter(
    prefix="/avatars",
    tags=["avatars"],
)


@router.post("/user")
async def upload_user_avatar(
    username: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload the current user's avatar. Users may only set their own."""
    if username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change another user's avatar"
        )

    await save_avatar(USER_AVATAR_PREFIX, current_user.username, file)

    return {"message": "Avatar uploaded"}


@router.get("/user")
def get_user_avatar(
    username: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve a user's avatar. Requires auth, but any authenticated user may fetch anyone's."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return stream_avatar(USER_AVATAR_PREFIX, user.username)


@router.delete("/user")
def remove_user_avatar(
    username: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    """Delete the current user's avatar. Users may only delete their own."""
    if username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's avatar"
        )

    delete_avatar(USER_AVATAR_PREFIX, current_user.username)

    return {"message": "Avatar deleted"}


@router.post("/framily")
async def upload_framily_avatar(
    framily_code: str = Query(..., min_length=8, max_length=8),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a framily's avatar. Admin only."""
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

    await save_avatar(FRAMILY_AVATAR_PREFIX, framily.code, file)

    return {"message": "Avatar uploaded"}


@router.get("/framily")
def get_framily_avatar(
    framily_code: str = Query(..., min_length=8, max_length=8),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve a framily's avatar. Members only."""
    framily = db.query(Framily).filter(Framily.code == framily_code).first()
    if not framily:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framily not found."
        )

    membership = get_membership(db, current_user.id, framily.id)
    if not is_member(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this framily."
        )

    return stream_avatar(FRAMILY_AVATAR_PREFIX, framily.code)


@router.delete("/framily")
def remove_framily_avatar(
    framily_code: str = Query(..., min_length=8, max_length=8),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a framily's avatar. Admin only."""
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

    delete_avatar(FRAMILY_AVATAR_PREFIX, framily.code)

    return {"message": "Avatar deleted"}
