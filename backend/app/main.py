from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.cache import close_cache, connect_cache
from app.core.database import close_db, connect_db
from app.core.middleware import LoggingMiddleware, logger
from app.api import admin, ai_chats, auth, goals, recurring_payments, reports, tracker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await connect_cache()
    logger.info("%s v%s started", settings.APP_NAME, settings.APP_VERSION)
    yield
    await close_db()
    await close_cache()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal finance platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Logging middleware (wraps every request) ───────────────────────────────────
app.add_middleware(LoggingMiddleware)

# ── Global exception handlers ──────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None) or {},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(goals.router)
app.include_router(admin.router)
app.include_router(recurring_payments.router)
app.include_router(ai_chats.router)
app.include_router(tracker.router)


# ── Health checks ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health", tags=["Health"])
async def health():
    from app.core.cache import get_redis
    from app.core.database import get_database

    db_status = "connected"
    try:
        await get_database().command("ping")
    except Exception:
        db_status = "disconnected"

    redis_status = "connected"
    try:
        redis = get_redis()
        if redis:
            await redis.ping()
        else:
            redis_status = "disabled"
    except Exception:
        redis_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "mongodb": db_status,
        "redis": redis_status,
    }
