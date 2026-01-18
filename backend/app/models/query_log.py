from sqlalchemy import Column, String, Text, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from datetime import datetime
import uuid

from app.db.base import Base


class QueryLog(Base):
    """Comprehensive query logging for admin dashboard"""
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))

    # User input
    user_question = Column(Text, nullable=False)

    # SQL generation
    generated_sql = Column(Text)
    sql_generation_time_ms = Column(Integer)
    sql_tokens_used = Column(Integer)

    # Execution
    execution_status = Column(String(20))  # 'success', 'failed', 'timeout'
    execution_time_ms = Column(Integer)
    rows_returned = Column(Integer)
    bytes_processed = Column(BigInteger)  # BigQuery bytes scanned

    # Errors
    error_message = Column(Text)
    error_type = Column(String(100))

    # Context
    langchain_trace_id = Column(String(255))
    model_used = Column(String(50))

    # Metadata
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
