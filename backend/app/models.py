from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    routes = relationship("MockRoute", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("MockRequestLog", back_populates="project", cascade="all, delete-orphan")


class MockRoute(Base, TimestampMixin):
    __tablename__ = "mock_routes"
    __table_args__ = (UniqueConstraint("project_id", "method", "path", name="uq_project_method_path"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    method = Column(String(16), nullable=False, index=True)
    path = Column(String(1024), nullable=False, index=True)
    description = Column(Text, nullable=True)
    expected_headers_json = Column(Text, nullable=True)
    expected_body_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    project = relationship("Project", back_populates="routes")
    responses = relationship("MockResponse", back_populates="mock_route", cascade="all, delete-orphan")
    logs = relationship("MockRequestLog", back_populates="mock_route")


class MockResponse(Base, TimestampMixin):
    __tablename__ = "mock_responses"

    id = Column(Integer, primary_key=True, index=True)
    mock_route_id = Column(Integer, ForeignKey("mock_routes.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status_code = Column(Integer, default=200, nullable=False)
    headers_json = Column(Text, nullable=True)
    body_json = Column(Text, nullable=True)
    condition_json = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
    delay_ms = Column(Integer, default=0, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    mock_route = relationship("MockRoute", back_populates="responses")
    logs = relationship("MockRequestLog", back_populates="matched_response")


class MockRequestLog(Base):
    __tablename__ = "mock_request_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    mock_route_id = Column(Integer, ForeignKey("mock_routes.id"), nullable=True, index=True)
    matched_response_id = Column(Integer, ForeignKey("mock_responses.id"), nullable=True, index=True)
    method = Column(String(16), nullable=False)
    path = Column(String(2048), nullable=False)
    query_json = Column(Text, nullable=True)
    headers_json = Column(Text, nullable=True)
    body_json = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    project = relationship("Project", back_populates="logs")
    mock_route = relationship("MockRoute", back_populates="logs")
    matched_response = relationship("MockResponse", back_populates="logs")
