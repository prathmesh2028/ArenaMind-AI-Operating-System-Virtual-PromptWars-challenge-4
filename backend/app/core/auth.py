"""
JWT Authentication Utilities
-----------------------------
Handles token creation, verification, and user identity extraction.
All tokens are signed with HMAC-SHA256 using the app SECRET_KEY.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config import settings

logger = logging.getLogger("arenamind.auth")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_HOURS = 168  # 7 days


# ---------------------------------------------------------------------------
# Token Creation
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str,
    role: str,
    email: str,
    display_name: Optional[str] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: User UUID string (becomes the 'sub' claim).
        role: User role name (e.g., 'ADMIN', 'OPERATIONS').
        email: User email.
        display_name: Optional display name.
        extra_claims: Optional additional payload claims.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "email": email,
        "display_name": display_name or email,
        "iat": now,
        "exp": expire,
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Access token created for user {subject} (role={role})")
    return token


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh token containing only the user ID."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Token Verification
# ---------------------------------------------------------------------------

def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Returns:
        Decoded payload dict.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid or tampered with.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify an access token specifically.

    Raises:
        ValueError: If token type is not 'access'.
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise InvalidTokenError("Token is not an access token")
    return payload


def verify_refresh_token(token: str) -> str:
    """
    Decode and verify a refresh token.

    Returns:
        The user ID (subject) from the token.

    Raises:
        ValueError: If token type is not 'refresh'.
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise InvalidTokenError("Token is not a refresh token")
    return payload["sub"]
