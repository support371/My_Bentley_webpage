import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.database import init_db
from app.api.routes import auth, dashboard, events, webhooks, admin
from app.db.seed import seed_initial_data

setup_logging()
logger = logging.getLogger("itwin_ops")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    await seed_initial_data()
    logger.info("Database ready")
    yield
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-capable Bentley iTwin event intelligence platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(webhooks.router)
app.include_router(admin.router)


@app.get("/health", tags=["System"])
async def health():
    from datetime import datetime
    from app.db.database import AsyncSessionLocal
    from sqlalchemy import text
    db_ok = True
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "ok" if db_ok else "error",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bentley_configured": bool(settings.BENTLEY_CLIENT_ID),
    }


@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return RedirectResponse("/dashboard")
