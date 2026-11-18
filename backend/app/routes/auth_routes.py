from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import (
    CurrentUser,
    get_or_create_dev_user,
    get_or_create_local_operator,
    login_user,
    logout_user,
    verify_local_password,
)
from app.db import get_db
from app.schemas import LocalLoginIn, UserOut
from app.settings import get_settings

router = APIRouter(tags=["auth"])


@router.get("/api/v1/auth/me", response_model=UserOut)
def auth_me(user: CurrentUser):
    return user


@router.post("/api/v1/auth/login", response_model=UserOut)
def auth_local_login(request: Request, payload: LocalLoginIn, db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.auth_mode != "local":
        raise HTTPException(status_code=404, detail="Local login disabled")
    if not verify_local_password(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user = get_or_create_local_operator(db)
    login_user(request, user.id)
    return user


@router.get("/auth/dev-login")
def auth_dev_login(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.auth_mode != "dev":
        raise HTTPException(status_code=404)
    user = get_or_create_dev_user(db)
    login_user(request, user.id)
    return RedirectResponse(url="/")


@router.post("/api/v1/auth/logout")
def auth_logout(request: Request):
    logout_user(request)
    return {"ok": True}