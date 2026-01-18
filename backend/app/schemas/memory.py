from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class GlobalInstructionCreate(BaseModel):
    instruction_text: str
    category: Optional[str] = None
    priority: int = 0


class GlobalInstructionUpdate(BaseModel):
    instruction_text: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class GlobalInstructionResponse(BaseModel):
    id: UUID
    instruction_text: str
    category: Optional[str]
    priority: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectMemoryCreate(BaseModel):
    memory_type: str  # 'business_rule', 'calculation', 'domain_knowledge'
    key: str
    content: str


class ProjectMemoryUpdate(BaseModel):
    memory_type: Optional[str] = None
    key: Optional[str] = None
    content: Optional[str] = None


class ProjectMemoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    memory_type: str
    key: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectInstructionCreate(BaseModel):
    instruction_text: str
    priority: int = 0


class ProjectInstructionUpdate(BaseModel):
    instruction_text: Optional[str] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class ProjectInstructionResponse(BaseModel):
    id: UUID
    project_id: UUID
    instruction_text: str
    priority: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
