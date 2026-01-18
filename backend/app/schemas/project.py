from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    bigquery_project_id: Optional[str] = None
    bigquery_dataset: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bigquery_project_id: Optional[str] = None
    bigquery_dataset: Optional[str] = None


class BigQueryCredentials(BaseModel):
    """BigQuery service account credentials"""
    credentials_json: str  # Service account JSON as string


class ProjectResponse(ProjectBase):
    id: UUID
    owner_id: UUID
    bigquery_project_id: Optional[str]
    bigquery_dataset: Optional[str]
    schema_last_updated: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchemaInfo(BaseModel):
    """Schema information for a table"""
    table_name: str
    columns: list[Dict[str, Any]]
    row_count: Optional[int] = None
