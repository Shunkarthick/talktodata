from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models import User, Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    BigQueryCredentials,
    SchemaInfo,
)
from app.api.deps import get_current_user
from app.services.bigquery.bigquery_service import BigQueryService
from app.core.logging import logger

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project"""
    project = Project(
        owner_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        bigquery_project_id=project_data.bigquery_project_id,
        bigquery_dataset=project_data.bigquery_dataset,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(f"Project created: {project.name} by {current_user.email}")

    return project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for current user"""
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project by ID"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.bigquery_project_id is not None:
        project.bigquery_project_id = project_data.bigquery_project_id
    if project_data.bigquery_dataset is not None:
        project.bigquery_dataset = project_data.bigquery_dataset

    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    db.delete(project)
    db.commit()

    logger.info(f"Project deleted: {project.name}")


@router.post("/{project_id}/bigquery/connect")
async def connect_bigquery(
    project_id: UUID,
    credentials: BigQueryCredentials,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload BigQuery credentials and test connection"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Store encrypted credentials (in production, encrypt this!)
    project.credentials_encrypted = credentials.credentials_json

    # Test connection
    bigquery_service = BigQueryService(project_id=str(project_id), db_session=db)

    try:
        connection_ok = await bigquery_service.test_connection()
        if not connection_ok:
            raise Exception("Connection test failed")

        # Extract schema
        schema = await bigquery_service.get_schema()
        project.schema_cache = schema
        project.schema_last_updated = datetime.utcnow()

        db.commit()

        logger.info(f"BigQuery connected for project: {project.name}")

        return {
            "status": "connected",
            "tables_found": len(schema),
            "message": "BigQuery connection successful",
        }

    except Exception as e:
        logger.error(f"BigQuery connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection failed: {str(e)}",
        )


@router.get("/{project_id}/bigquery/schema")
async def get_schema(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cached BigQuery schema"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.schema_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not available. Please connect to BigQuery first.",
        )

    return project.schema_cache


@router.post("/{project_id}/bigquery/refresh")
async def refresh_schema(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Refresh BigQuery schema cache"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    bigquery_service = BigQueryService(project_id=str(project_id), db_session=db)

    try:
        schema = await bigquery_service.get_schema()
        project.schema_cache = schema
        project.schema_last_updated = datetime.utcnow()

        db.commit()

        return {
            "status": "refreshed",
            "tables_found": len(schema),
            "updated_at": project.schema_last_updated,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schema refresh failed: {str(e)}",
        )
