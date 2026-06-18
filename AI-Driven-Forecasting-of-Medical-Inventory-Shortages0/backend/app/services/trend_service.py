from typing import List, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.settings import settings
from app.core.exception_handler import MLInferenceException, ValidationException
from app.repositories import trend_repository
from app.schemas.trend_schema import TrendComputeRequest, TrendResponse
from app.utils.date_utils import utc_now
from app.utils.validation_utils import validate_pagination


def to_trend_response(trend: dict) -> TrendResponse:
    return TrendResponse(
        id=str(trend["_id"]),
        item_id=trend.get("item_id"),
        facility_id=trend.get("facility_id"),
        period=trend["period"],
        forecast_periods=int(trend["forecast_periods"]),
        forecast_rows=trend["forecast_rows"],
        computed_at=trend["computed_at"],
        config_used=trend["config_used"],
    )


async def compute_forecast(
    db: AsyncIOMotorDatabase,
    request: TrendComputeRequest,
    current_user_id: str,
) -> TrendResponse:
    from ml.src.inference.forecast_demand import forecast_demand

    config_path = f"{settings.ML_CONFIGS_PATH}/prophet_config.yaml"

    try:
        forecast_df = forecast_demand(config_path=config_path)
    except Exception as exc:
        raise MLInferenceException("Demand forecast failed") from exc

    if forecast_df is None or forecast_df.empty:
        raise ValidationException("Forecast output is empty")

    forecast_rows = []

    for _, row in forecast_df.iterrows():
        forecast_rows.append(
            {
                "ds": row["ds"].to_pydatetime()
                if hasattr(row["ds"], "to_pydatetime")
                else row["ds"],
                "yhat": float(row["yhat"]),
                "yhat_lower": float(row["yhat_lower"]),
                "yhat_upper": float(row["yhat_upper"]),
            }
        )

    now = utc_now()

    trend_doc = {
        "item_id": request.item_id,
        "facility_id": request.facility_id,
        "period": request.period,
        "forecast_periods": len(forecast_rows),
        "forecast_rows": forecast_rows,
        "computed_at": now,
        "config_used": {
            "config_path": config_path,
        },
    }

    saved = await trend_repository.upsert(
        db=db,
        item_id=request.item_id,
        facility_id=request.facility_id,
        period=request.period,
        data=trend_doc,
    )

    return to_trend_response(saved)


async def get_trends(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    period: str,
) -> List[TrendResponse]:
    trends = await trend_repository.get_for_item(
        db=db,
        item_id=item_id,
        facility_id=facility_id,
        period=period,
    )

    return [to_trend_response(trend) for trend in trends]


async def list_trends(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
) -> Tuple[List[TrendResponse], int]:
    page, limit = validate_pagination(page, limit)

    trends, total = await trend_repository.get_all(
        db=db,
        page=page,
        limit=limit,
    )

    return [to_trend_response(trend) for trend in trends], total