from __future__ import annotations

import hmac
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, UserRole
from app.settings import get_settings

LOCAL_OPERATOR_EMAIL = "root@case-audit.local"


def get_session_user_id(request: Request) -> Optional[int]:
    return request.session.get("user_id")


def login_user(request: Request, user_id: int) -> None:
    request.session["user_id"] = user_id


def logout_user(request: Request) -> None:
    request.session.clear()


def verify_local_password(username: str, password: str) -> bool:
    settings = get_settings()
    if not settings.local_auth_password:
        return False
    return hmac.compare_digest(username, settings.local_auth_username) and hmac.compare_digest(
        password, settings.local_auth_password
    )


def get_or_create_local_operator(db: Session) -> User:
    user = db.query(User).filter(User.email == LOCAL_OPERATOR_EMAIL).one_or_none()
    if user:
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user
    user = User(
        email=LOCAL_OPERATOR_EMAIL,
        display_name="root",
        role=UserRole.admin.value,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_dev_user(db: Session) -> User:
    settings = get_settings()
    user = db.query(User).filter(User.email == settings.dev_user_email).one_or_none()
    if user:
        return user
    user = User(
        email=settings.dev_user_email,
        display_name=settings.dev_user_name,
        role=settings.dev_user_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    settings = get_settings()
    if settings.auth_mode == "dev":
        return get_or_create_dev_user(db)
    if settings.auth_mode == "none":
        return get_or_create_dev_user(db)

    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]