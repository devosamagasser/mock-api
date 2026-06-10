from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def normalize_path(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError("Path is required")
    return value if value.startswith("/") else f"/{value}"


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    is_active: bool = True

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().lower() if value is not None else None


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MockRouteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    method: str = Field(..., min_length=1, max_length=16)
    path: str
    description: Optional[str] = None
    expected_headers_json: Optional[JsonValue] = None
    expected_body_json: Optional[JsonValue] = None
    is_active: bool = True

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return normalize_path(value)


class MockRouteCreate(MockRouteBase):
    pass


class MockRouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    method: Optional[str] = Field(None, min_length=1, max_length=16)
    path: Optional[str] = None
    description: Optional[str] = None
    expected_headers_json: Optional[JsonValue] = None
    expected_body_json: Optional[JsonValue] = None
    is_active: Optional[bool] = None

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value is not None else None

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: Optional[str]) -> Optional[str]:
        return normalize_path(value) if value is not None else None


class MockRouteOut(MockRouteBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MockResponseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    status_code: int = Field(200, ge=100, le=599)
    headers_json: Optional[JsonValue] = None
    body_json: Optional[JsonValue] = None
    condition_json: Optional[JsonValue] = None
    priority: int = 100
    delay_ms: int = Field(0, ge=0, le=120000)
    is_default: bool = False
    is_active: bool = True


class MockResponseCreate(MockResponseBase):
    pass


class MockResponseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status_code: Optional[int] = Field(None, ge=100, le=599)
    headers_json: Optional[JsonValue] = None
    body_json: Optional[JsonValue] = None
    condition_json: Optional[JsonValue] = None
    priority: Optional[int] = None
    delay_ms: Optional[int] = Field(None, ge=0, le=120000)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class MockResponseOut(MockResponseBase):
    id: int
    mock_route_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MockRequestLogOut(BaseModel):
    id: int
    project_id: Optional[int]
    mock_route_id: Optional[int]
    matched_response_id: Optional[int]
    method: str
    path: str
    query_json: Optional[JsonValue]
    headers_json: Optional[JsonValue]
    body_json: Optional[JsonValue]
    status_code: int
    created_at: datetime
    project_name: Optional[str] = None
    route_name: Optional[str] = None
    response_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_projects: int
    total_routes: int
    total_active_routes: int
    total_request_logs: int
    latest_logs: list[MockRequestLogOut]
