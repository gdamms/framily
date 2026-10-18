from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from core.database import get_db
from core.config import settings
from core.mail import send_email_safely
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    password_fingerprint_matches,
)
from models import User
from schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserInfo,
    AuthFeatures,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token (cookie first, Bearer fallback)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("auth_token")
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Purpose-scoped tokens (e.g. password reset) are not session tokens.
        if payload.get("purpose"):
            raise credentials_exception
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    # Create new user
    hashed_password = hash_password(request.password)
    db_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password,
        display_name=request.username  # Default display name is username
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access token. New accounts stay logged in by default, same as
    # the default for /login.
    access_token = create_access_token(data={"sub": str(db_user.id)}, infinite=True)
    return {"token": access_token}


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login a user by username or email."""
    # Try to find user by username first, then by email
    db_user = db.query(User).filter(User.username == request.username_or_email).first()
    if not db_user:
        # Try email lookup if username lookup failed
        db_user = db.query(User).filter(User.email == request.username_or_email).first()

    if not db_user:
        # User not found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(request.password, db_user.hashed_password):
        # Password does not match
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create access token. Stays logged in indefinitely unless the user
    # unticked "stay logged in", in which case it expires like a normal
    # short-lived session.
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, infinite=request.remember_me
    )
    return {"token": access_token}


@router.get("/me", response_model=UserInfo)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserInfo(
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name
    )


@router.get("/features", response_model=AuthFeatures)
def get_features():
    """Optional auth features enabled on this server."""
    return {"password_reset": settings.smtp_enabled}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Email a password reset link to the account with this address, if any.

    Always returns the same response so it can't be used to probe which
    emails are registered; the email is sent in the background for the same
    reason (no timing difference) and so a slow SMTP server doesn't block.
    """
    if not settings.smtp_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is not available on this server",
        )

    db_user = db.query(User).filter(User.email == request.email).first()
    if db_user:
        token = create_password_reset_token(db_user.id, db_user.hashed_password)
        link = f"{settings.public_url}/?{urlencode({'reset_token': token})}"
        body = (
            f"Hi {db_user.display_name},\n\n"
            "Someone (hopefully you) asked to reset your Framily password.\n"
            "Open this link to choose a new one:\n\n"
            f"{link}\n\n"
            f"The link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes and can only be used once.\n"
            "If you didn't ask for this, you can ignore this email.\n"
        )
        background_tasks.add_task(send_email_safely, db_user.email, "Reset your Framily password", body)

    return {"message": "If an account exists for this email, a reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Set a new password using a token from a password reset email."""
    invalid_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This reset link is invalid or has expired",
    )

    decoded = decode_password_reset_token(request.token)
    if decoded is None:
        raise invalid_token
    user_id, fingerprint = decoded

    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None or not password_fingerprint_matches(fingerprint, db_user.hashed_password):
        raise invalid_token

    db_user.hashed_password = hash_password(request.password)
    db.commit()
    return {"message": "Password has been reset"}
