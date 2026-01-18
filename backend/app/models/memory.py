from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class GlobalInstruction(Base):
    """Global-level agent instructions (system-wide)"""
    __tablename__ = "global_instructions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instruction_text = Column(Text, nullable=False)
    category = Column(String(100))  # 'sql_safety', 'optimization', 'formatting'
    priority = Column(Integer, default=0)  # Lower number = higher priority
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectMemory(Base):
    """Project-level memory (business rules, calculations)"""
    __tablename__ = "project_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    memory_type = Column(String(50))  # 'business_rule', 'calculation', 'domain_knowledge'
    key = Column(String(255), nullable=False)  # e.g., "revenue_calculation"
    content = Column(Text, nullable=False)  # e.g., "Revenue = gross_sales - returns"
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="project_memory")


class ProjectInstruction(Base):
    """Project-level agent instructions"""
    __tablename__ = "project_instructions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    instruction_text = Column(Text, nullable=False)
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="project_instructions")
