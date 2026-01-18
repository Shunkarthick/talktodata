from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class QueryRequest(BaseModel):
    """Request to convert text to SQL and execute"""
    project_id: UUID
    question: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None
    model: str = "claude-3-5-sonnet-20241022"
    stream: bool = True


class SQLExecuteRequest(BaseModel):
    """Request to execute SQL directly"""
    project_id: UUID
    sql: str
    conversation_id: Optional[UUID] = None


class QueryResult(BaseModel):
    """Query execution result"""
    sql: str
    rows: List[Dict[str, Any]]
    schema: List[Dict[str, str]]  # [{"name": "col1", "type": "STRING"}, ...]
    rows_returned: int
    execution_time_ms: int
    bytes_processed: Optional[int] = None


class QueryResponse(BaseModel):
    """Complete query response"""
    query_id: UUID
    sql: str
    result: Optional[QueryResult] = None
    error: Optional[str] = None
    insights: Optional[str] = None
    suggested_chart: Optional[Dict[str, Any]] = None
    tokens_used: int
    sql_generation_time_ms: int
    total_time_ms: int


class SavedQueryCreate(BaseModel):
    """Save a query as template"""
    project_id: UUID
    name: str
    description: Optional[str] = None
    sql_query: str
    is_template: bool = False


class SavedQueryResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    sql_query: str
    is_template: bool
    created_at: datetime

    class Config:
        from_attributes = True
