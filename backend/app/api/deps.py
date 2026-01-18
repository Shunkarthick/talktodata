from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.session import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models import User, APIKey
from app.core.security import verify_api_key

security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None),
) -> User:
    """
    Get current authenticated user
    Supports both JWT tokens and API keys
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try API key first
    if x_api_key:
        api_key = db.query(APIKey).filter(APIKey.key_prefix == x_api_key[:10]).first()
        if api_key and verify_api_key(x_api_key, api_key.key_hash):
            if not api_key.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key is inactive",
                )
            user = db.query(User).filter(User.id == api_key.user_id).first()
            if user:
                return user

    # Try JWT token
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception

            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise credentials_exception

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user",
                )

            return user

        except JWTError:
            raise credentials_exception

    raise credentials_exception


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify current user is a superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
