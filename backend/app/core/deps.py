"""
FastAPI Dependencies
--------------------
Reusable dependency functions injected into route handlers via Depends().

Provides:
  - get_current_user(): Extract & validate JWT from Authorization header
  - require_role(*roles): Factory for role-based access guards
  - get_db(): Database session (re-exported for convenience)
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.database import get_db
from app.models import User

logger = logging.getLogger("arenamind.deps")

# Bearer token extractor
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Current User Dependency
# ---------------------------------------------------------------------------

class CurrentUser:
    """Lightweight user identity object attached to every authenticated request."""

    def __init__(self, user: User) -> None:
        self.id = str(user.id)
        self.email = user.email
        self.display_name = user.display_name
        self.role = user.role.name  # eager-loaded via relationship


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    Validate the Bearer JWT from the Authorization header and return the
    corresponding CurrentUser. Raises 401 if the token is missing/invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = verify_access_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
        )

    return CurrentUser(user)


# ---------------------------------------------------------------------------
# Role-Based Access Guard Factory
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: str):
    """
    Dependency factory that enforces role-based access control.

    Usage:
        @router.get("/admin-only")
        def admin_route(user: CurrentUser = Depends(require_role("ADMIN"))):
            ...
    """
    def _check_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Access denied: user {current_user.email} (role={current_user.role}) "
                f"attempted to access route requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}.",
            )
        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Convenience role shortcuts
# ---------------------------------------------------------------------------

def require_admin(user: CurrentUser = Depends(require_role("ADMIN"))) -> CurrentUser:
    return user

def require_operations(user: CurrentUser = Depends(require_role("ADMIN", "OPERATIONS"))) -> CurrentUser:
    return user

def require_staff(
    user: CurrentUser = Depends(require_role("ADMIN", "OPERATIONS", "VOLUNTEER", "MEDICAL", "SECURITY"))
) -> CurrentUser:
    return user
