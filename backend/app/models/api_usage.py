from sqlalchemy import Column, String, Text, Integer, BigInteger, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from datetime import datetime
import uuid

from app.db.base import Base


class APIUsage(Base):
    """API usage tracking"""
    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Endpoint info
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10))  # GET, POST, etc.

    # Response
    status_code = Column(Integer)
    response_time_ms = Column(Integer)

    # Quotas
    tokens_used = Column(Integer, default=0)
    bigquery_bytes = Column(BigInteger, default=0)

    # Auth method
    auth_type = Column(String(20))  # 'jwt', 'api_key', 'session'
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"))

    # Metadata
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ErrorLog(Base):
    """Error logging"""
    __tablename__ = "error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    # Error details
    error_type = Column(String(100), index=True)
    error_message = Column(Text)
    stack_trace = Column(Text)

    # Context
    endpoint = Column(String(255))
    request_payload = Column(JSON)

    # Severity
    severity = Column(String(20), index=True)  # 'critical', 'error', 'warning'

    # Resolution
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
