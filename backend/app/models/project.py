from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # BigQuery connection
    bigquery_project_id = Column(String(255))
    bigquery_dataset = Column(String(255))
    credentials_encrypted = Column(Text)  # Encrypted service account JSON

    # Schema cache (JSON)
    schema_cache = Column(JSON, default={})
    schema_last_updated = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    project_memory = relationship("ProjectMemory", back_populates="project", cascade="all, delete-orphan")
    project_instructions = relationship("ProjectInstruction", back_populates="project", cascade="all, delete-orphan")
