from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models import User, Project
from app.schemas.query import QueryRequest, SQLExecuteRequest, QueryResponse
from app.api.deps import get_current_user
from app.services.query_service import QueryService
from app.core.logging import logger

router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    query_request: QueryRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Main endpoint: Ask a question in natural language
    - Converts to SQL using LangChain + Claude
    - Executes on BigQuery
    - Returns results with insights
    """
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == query_request.project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify BigQuery is configured
    if not project.credentials_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BigQuery not configured for this project",
        )

    # Get client IP and user agent
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")

    # Process question
    query_service = QueryService(db_session=db)

    try:
        result = await query_service.process_question(
            project_id=str(query_request.project_id),
            user_id=str(current_user.id),
            question=query_request.question,
            conversation_id=str(query_request.conversation_id) if query_request.conversation_id else None,
            model=query_request.model,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}",
        )


@router.post("/execute-sql")
async def execute_sql(
    sql_request: SQLExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute SQL directly without text-to-SQL conversion
    Useful for:
    - Editing generated SQL
    - Advanced users who prefer writing SQL
    - API integrations
    """
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == sql_request.project_id,
        Project.owner_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Execute SQL
    query_service = QueryService(db_session=db)

    try:
        result = await query_service.execute_sql_directly(
            project_id=str(sql_request.project_id),
            user_id=str(current_user.id),
            sql=sql_request.sql,
            conversation_id=str(sql_request.conversation_id) if sql_request.conversation_id else None,
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL execution failed: {str(e)}",
        )


@router.get("/history")
async def get_query_history(
    project_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get query history for user"""
    from app.models import QueryLog

    query = db.query(QueryLog).filter(QueryLog.user_id == current_user.id)

    if project_id:
        query = query.filter(QueryLog.project_id == project_id)

    logs = query.order_by(QueryLog.created_at.desc()).limit(limit).offset(offset).all()

    return {
        "total": query.count(),
        "logs": logs,
    }
