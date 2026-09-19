"""Schemas shared by more than one boundary."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """One field-level validation problem."""

    field: str = Field(description="Location of the offending value, e.g. body.email")
    message: str


class ErrorBody(BaseModel):
    """The contents of an error response."""

    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable message, safe to display")
    request_id: str = Field(description="Correlation id, also returned as X-Request-ID")
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="Only present for validation failures",
    )


class ErrorResponse(BaseModel):
    """Every non-2xx response has this shape."""

    error: ErrorBody


class Page[ItemT](BaseModel):
    """One page of results.

    Offset pagination is used because the datasets here are per-user and small.
    It is not stable under concurrent inserts; a cursor would be, and is the
    change to make if these lists ever grow.
    """

    items: list[ItemT]
    total: int = Field(description="Total number of rows matching the query")
    limit: int
    offset: int
