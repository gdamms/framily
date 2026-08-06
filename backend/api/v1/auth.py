from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from core.database import get_db
from core.config import settings
from core.security import hash_password, verify_password, create_access_token
from models import User
from schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse, UserInfo

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
