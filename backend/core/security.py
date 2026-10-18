import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None, infinite: bool = False
) -> str:
    """Create a JWT access token. If infinite is True, the token is issued
    with no "exp" claim at all ("stay logged in"), so it never expires;
    otherwise it expires after expires_delta (or ACCESS_TOKEN_EXPIRE_MINUTES
    if not given)."""
    to_encode = data.copy()
    if not infinite:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


PASSWORD_RESET_PURPOSE = "password_reset"


def _password_fingerprint(hashed_password: str) -> str:
    """Short digest of the stored password hash, embedded in reset tokens so
    that a token stops working as soon as the password changes (single use)."""
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def create_password_reset_token(user_id: int, hashed_password: str) -> str:
    """Create a short-lived JWT allowing its holder to reset one user's password."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "purpose": PASSWORD_RESET_PURPOSE,
        "pwd": _password_fingerprint(hashed_password),
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_password_reset_token(token: str) -> Optional[tuple[int, str]]:
    """Return (user_id, password_fingerprint) for a valid, unexpired reset
    token, or None. The caller must still compare the fingerprint against the
    user's current hash with password_fingerprint_matches()."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("purpose") != PASSWORD_RESET_PURPOSE or "exp" not in payload:
        return None
    try:
        return int(payload["sub"]), str(payload["pwd"])
    except (KeyError, TypeError, ValueError):
        return None


def password_fingerprint_matches(fingerprint: str, hashed_password: str) -> bool:
    return hmac.compare_digest(fingerprint, _password_fingerprint(hashed_password))
