from contextlib import asynccontextmanager
from pathlib import Path
import sys
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "ml"))

from app.api.v1.api_router import api_router
from app.config.database import connect_db, close_db_connection, get_db_client
from app.config.settings import settings
from app.core.exception_handler import register_exception_handlers
from app.core.password_handler import hash_password
from app.core.permissions import ADMIN_ALL
from app.db.indexes import create_all_indexes
from app.middleware.audit_middleware import AuditMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.repositories import role_repository, user_repository
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def ensure_admin_user() -> None:
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
        return

    db = get_db_client()[settings.MONGO_DB_NAME]
    admin_role = await role_repository.get_by_name(db, settings.ADMIN_ROLE_NAME)
    if admin_role is None:
        admin_role = await role_repository.create(
            db,
            {
                "name": settings.ADMIN_ROLE_NAME,
                "permissions": [ADMIN_ALL],
                "description": "Administrator role",
                "created_at": utc_now(),
            },
        )

    existing_user = await user_repository.get_by_email(
        db, str(settings.ADMIN_EMAIL).lower().strip()
    )
    if existing_user:
        return

    user_doc = {
        "email": str(settings.ADMIN_EMAIL).lower().strip(),
        "password_hash": hash_password(settings.ADMIN_PASSWORD),
        "full_name": settings.ADMIN_FULL_NAME,
        "employee_id": settings.ADMIN_EMPLOYEE_ID,
        "role_id": admin_role["_id"],
        "role_name": admin_role["name"],
        "department": settings.ADMIN_DEPARTMENT,
        "is_active": True,
        "last_login": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    await user_repository.create(db, user_doc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    client = get_db_client()
    await client.admin.command("ping")
    logger.info("MongoDB connected successfully")

    app.state.predictor = None
    app.state.model_version = "unknown"

    try:
        metadata_path = BASE_DIR / settings.ML_ARTIFACTS_PATH / "model_metadata.json"

        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as file:
                metadata = json.load(file)
                app.state.model_version = str(
                    metadata.get("model_version")
                    or metadata.get("version")
                    or "unknown"
                )

        from ml.src.inference.realtime_predict import RealtimeStockoutPredictor

        app.state.predictor = RealtimeStockoutPredictor(
            config_path=str(BASE_DIR / settings.ML_CONFIGS_PATH / "xgboost_config.yaml"),
            risk_config_path=str(BASE_DIR / settings.ML_CONFIGS_PATH / "risk_engine_config.yaml"),
        )

        logger.info(
            f"RealtimeStockoutPredictor initialized successfully, "
            f"model_version={app.state.model_version}"
        )

    except Exception as exc:
        logger.critical(f"ML predictor initialization failed: {exc}")
    await create_all_indexes()
    await ensure_admin_user()
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