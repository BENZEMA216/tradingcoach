"""
Common schemas used across the application
"""

from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List, Optional
from datetime import date

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class DateRangeParams(BaseModel):
    """Date range filter parameters"""
    date_start: Optional[date] = None
    date_end: Optional[date] = None


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    success: bool = True
