"""Shared schema primitives used across all routers."""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class OrmBase(BaseModel):
    """Base model with ORM mode enabled for SQLAlchemy compatibility."""
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response envelope."""
    total: int
    page: int
    page_size: int
    items: List[T]


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    status_code: int
    error: str
    message: str
