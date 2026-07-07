"""
Authentication Router
----------------------
POST /auth/login   — Issue JWT tokens by email lookup (demo mode)
GET  /auth/me      — Return current user profile
POST /auth/refresh — Issue new access token from a valid refresh token
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, create_refresh_token, verify_refresh_token
from app.core.deps import CurrentUser, get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserProfile

logger = logging.getLogger("arenamind.routers.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
    description=(
        "**Demo Mode**: Supply a registered email address. "
        "The system looks up the user and issues a signed access + refresh token pair. "
        "No password is required for the hackathon demonstration environment."
    ),
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user: User | None = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if not user:
        logger.warning(f"Login failed: email not found — {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email address. Check the seed data for valid emails.",
        )

    # Eager-load role for token claims
    role_name = user.role.name if user.role else "FAN"

    access_token = create_access_token(
        subject=str(user.id),
        role=role_name,
        email=user.email,
        display_name=user.display_name,
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"Login successful: {user.email} (role={role_name})")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current authenticated user profile",
)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new access token",
)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

    try:
        user_id = verify_refresh_token(payload.refresh_token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {exc}",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    role_name = user.role.name if user.role else "FAN"
    new_access_token = create_access_token(
        subject=str(user.id),
        role=role_name,
        email=user.email,
        display_name=user.display_name,
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)
