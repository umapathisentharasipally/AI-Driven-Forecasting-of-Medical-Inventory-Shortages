from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "ml"))

from app.api.v1.api_router import api_router
from app.config.database import connect_db, close_db_connection, get_db_client
from app.config.settings import settings
from app.core.exception_handler import register_exception_handlers
from app.db.indexes import create_all_indexes
from app.middleware.audit_middleware import AuditMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    client = get_db_client()
    await client.admin.command("ping")
    logger.info("MongoDB connected successfully")

    app.state.predictor = None
    try:
        from src.inference.realtime_predict import RealtimeStockoutPredictor

        app.state.predictor = RealtimeStockoutPredictor()
        logger.info("RealtimeStockoutPredictor initialized successfully")
    except Exception as exc:
        logger.critical(f"ML predictor initialization failed: {exc}")

    await create_all_indexes()
    logger.info("MongoDB indexes initialized successfully")

    yield

    await close_db_connection()
    logger.info("MongoDB connection closed")


app = FastAPI(
    title="Medical Inventory Forecasting API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    db_status = "down"
    try:
        client = get_db_client()
        await client.admin.command("ping")
        db_status = "up"
    except Exception:
        db_status = "down"

    ml_status = "loaded" if getattr(app.state, "predictor", None) is not None else "not_loaded"
    overall_status = "healthy" if db_status == "up" else "unhealthy"

    return {
        "status": overall_status,
        "db": db_status,
        "ml_model": ml_status,
        "environment": settings.APP_ENV,
        "version": settings.APP_VERSION,
        "timestamp": utc_now().isoformat(),
    }