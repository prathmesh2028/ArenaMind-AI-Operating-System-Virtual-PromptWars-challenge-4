"""Authentication request/response schemas."""

from pydantic import BaseModel, Field
from app.schemas.common import OrmBase


class LoginRequest(BaseModel):
    """Login payload — email-based identity for demo environment."""
    email: str = Field(..., description="Registered user email address", examples=["manager@fifa.com"])


class TokenResponse(BaseModel):
    """Issued token pair after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_hours: int = 24


class RefreshRequest(BaseModel):
    """Refresh token request body."""
    refresh_token: str


class UserProfile(OrmBase):
    """Authenticated user's public profile."""
    id: str
    email: str
    display_name: str | None
    role: str

    @classmethod
    def from_orm_user(cls, user, role_name: str) -> "UserProfile":
        return cls(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=role_name,
        )
