from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.db import SessionLocal
from app.middleware.response_time import ResponseTimeMiddleware
from app.routes import audits, auth_routes, questionnaires, reports
from app.seed import seed_if_empty
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Customer Audit Service", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.is_production,
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ResponseTimeMiddleware)
    app.include_router(auth_routes.router)
    app.include_router(audits.router)
    app.include_router(questionnaires.router)
    app.include_router(reports.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready():
        from sqlalchemy import text

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:
            return {"status": "not_ready", "error": str(exc)}
        finally:
            db.close()
        return {"status": "ready"}

    static_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    index_html = static_dir / "index.html"
    if index_html.is_file():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        def spa_index():
            return FileResponse(index_html)

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            if full_path.startswith(
                ("api/", "auth/", "health", "ready", "docs", "openapi.json", "redoc")
            ):
                raise HTTPException(404)
            candidate = static_dir / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_html)

    return app


app = create_app()