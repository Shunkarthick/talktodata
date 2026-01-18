from fastapi import APIRouter

from app.api.v1.endpoints import auth, projects, queries

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
