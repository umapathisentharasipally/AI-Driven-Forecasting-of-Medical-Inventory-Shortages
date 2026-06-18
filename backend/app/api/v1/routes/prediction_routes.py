from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import MLInferenceException
from app.core.permissions import PREDICTION_READ, PREDICTION_RUN
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.prediction_schema import (
    BatchPredictRequest,
    PredictionFilter,
    RealtimePredictRequest,
)
from app.services import prediction_service

router = APIRouter()


@router.post("/realtime")
async def realtime_predict(
    data: RealtimePredictRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_RUN])),
):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise MLInferenceException("Realtime predictor is not initialized")

    prediction = await prediction_service.predict_realtime(
        db=db,
        request=data,
        predictor=predictor,
        model_version=getattr(request.app.state, "model_version", "unknown"),
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=prediction.model_dump(mode="json"),
        message="Realtime prediction completed successfully",
    )


@router.post("/batch")
async def batch_predict(
    data: BatchPredictRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_RUN])),
):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise MLInferenceException("Realtime predictor is not initialized")

    result = await prediction_service.predict_batch(
        db=db,
        request=data,
        predictor=predictor,
        model_version=getattr(request.app.state, "model_version", "unknown"),
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=result.model_dump(mode="json"),
        message="Batch prediction completed successfully",
    )


@router.get("/")
async def list_predictions(
    item_id: Optional[str] = Query(default=None),
    facility_id: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    filters = PredictionFilter(
        item_id=item_id,
        facility_id=facility_id,
        risk_level=risk_level,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    predictions, total = await prediction_service.get_predictions(db, filters)

    return paginated_response(
        data=[prediction.model_dump(mode="json") for prediction in predictions],
        total=total,
        page=page,
        limit=limit,
        message="Predictions fetched successfully",
    )


@router.get("/item/{item_id}")
async def get_latest_for_item(
    item_id: str,
    facility_id: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    prediction = await prediction_service.get_latest_for_item(
        db=db,
        item_id=item_id,
        facility_id=facility_id,
    )

    return success_response(
        data=prediction.model_dump(mode="json"),
        message="Latest item prediction fetched successfully",
    )


@router.get("/{id}")
async def get_prediction(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    prediction = await prediction_service.get_prediction_by_id(db, id)

    return success_response(
        data=prediction.model_dump(mode="json"),
        message="Prediction fetched successfully",
    )