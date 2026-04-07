import logging
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.database import init_db
from app.api.routes import auth, dashboard, events, webhooks, admin
from app.api.routes import integrations, itwins, mobile, imodels, launch_readiness, control_plane, agent
from app.db.seed import seed_initial_data
from app.models import integrations as _integrations_model  # ensure table is registered
from app.models import ops as _ops_model  # ensure table is registered

setup_logging()
logger = logging.getLogger("itwin_ops")
templates = Jinja2Templates(directory="app/templates")


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

app.add_middleware(GZipMiddleware, minimum_size=1024)

_cors_origins = [settings.PUBLIC_BASE_URL] if settings.PUBLIC_BASE_URL else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=bool(_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Rate limiting (in-memory, per IP per minute for /webhook) ─────────────────
_rate_buckets: dict = defaultdict(int)
_rate_bucket_ts: dict = {}
_RATE_LIMIT = settings.RATE_LIMIT_PER_MINUTE


def _check_rate_limit(ip: str) -> bool:
    now = int(time.time() // 60)
    key = f"{ip}:{now}"
    if _rate_bucket_ts.get(ip) != now:
        _rate_buckets[ip] = 0
        _rate_bucket_ts[ip] = now
    _rate_buckets[ip] += 1
    return _rate_buckets[ip] <= _RATE_LIMIT


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    if request.url.path == "/webhook" and request.method == "POST":
        ip = request.client.host if request.client else "unknown"
        if not _check_rate_limit(ip):
            logger.warning(f"Rate limit exceeded for {ip} on /webhook")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Max {_RATE_LIMIT} requests/minute."},
                headers={"Retry-After": "60"},
            )

    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration}ms"
    return response


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(webhooks.router)
app.include_router(admin.router)
app.include_router(integrations.router)
app.include_router(itwins.router)
app.include_router(mobile.router)
app.include_router(imodels.router)
app.include_router(launch_readiness.router)
app.include_router(control_plane.router)
app.include_router(agent.router)


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


def _error_response(request: Request, code: int, title: str, message: str, detail: str = ""):
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=code, content={"detail": message})
    try:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "code": code,
                "title": title,
                "message": message,
                "detail": detail,
            },
            status_code=code,
        )
    except Exception:
        return HTMLResponse(f"<h1>{code} — {title}</h1><p>{message}</p>", status_code=code)


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return _error_response(
        request, 404,
        "Page Not Found",
        f"The page at {request.url.path} doesn't exist. It may have been moved or the URL is incorrect.",
    )


@app.exception_handler(403)
async def forbidden(request: Request, exc):
    return _error_response(
        request, 403,
        "Access Forbidden",
        "You don't have permission to access this resource.",
    )


@app.exception_handler(500)
async def server_error(request: Request, exc):
    logger.error(f"500 on {request.url.path}: {exc}")
    return _error_response(
        request, 500,
        "Internal Server Error",
        "Something went wrong on our end. The error has been logged. Please try again in a moment.",
        detail=str(exc),
    )


@app.exception_handler(429)
async def too_many_requests(request: Request, exc):
    return _error_response(
        request, 429,
        "Too Many Requests",
        f"Rate limit exceeded. Please wait a moment before trying again.",
    )
