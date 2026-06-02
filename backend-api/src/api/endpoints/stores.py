"""
Purpose: FastAPI REST endpoints for Store Analytics.
Responsibilities:
- Define the HTTP routing schema for `/stores/{id}/*`.
- Inject the asynchronous database session securely.
- Handle HTTP exceptions, error logging, and input validation.
- Delegate complex database aggregations to the `AnalyticsService`.
Dependencies: fastapi, sqlalchemy
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.event import (
    AnalyticsFunnelResponse,
    AnalyticsHeatmapResponse,
    AnalyticsMetricsResponse,
)
from src.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stores", tags=["Store Analytics"])


@router.get(
    "/{store_id}/metrics",
    response_model=AnalyticsMetricsResponse,
    summary="Get Store KPIs",
    description="Returns high-level conversion, total entries, and live occupancy."
)
async def get_store_metrics(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> AnalyticsMetricsResponse:
    """
    Fetches the primary Key Performance Indicators for the dashboard.
    """
    try:
        service = AnalyticsService(db)
        return await service.get_daily_metrics(store_id)
    except ValueError as ve:
        # Handle specific domain errors (e.g., Store ID not found)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to fetch metrics for store {store_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during metric aggregation."
        )


@router.get(
    "/{store_id}/funnel",
    response_model=AnalyticsFunnelResponse,
    summary="Get Conversion Funnel",
    description="Returns the step-by-step visitor drop-off rate (Entry -> Dwell -> Checkout)."
)
async def get_store_funnel(
    store_id: uuid.UUID,
    start_time: datetime = Query(
        default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=1),
        description="Defaults to the last 24 hours"
    ),
    end_time: datetime = Query(
        default_factory=lambda: datetime.now(timezone.utc)
    ),
    db: AsyncSession = Depends(get_db)
) -> AnalyticsFunnelResponse:
    """
    Calculates the conversion funnel. Time windows are required via Query params 
    because funnels are highly sensitive to the temporal context (morning vs evening).
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="start_time must be strictly before end_time."
        )

    try:
        service = AnalyticsService(db)
        return await service.calculate_funnel(store_id, start_time, end_time)
    except Exception as e:
        logger.error(f"Failed to calculate funnel for store {store_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during funnel aggregation."
        )


@router.get(
    "/{store_id}/heatmap",
    response_model=AnalyticsHeatmapResponse,
    summary="Get Zone Popularity Heatmap",
    description="Returns normalized dwell time density across all store zones."
)
async def get_store_heatmap(
    store_id: uuid.UUID,
    start_time: datetime = Query(
        default_factory=lambda: datetime.now(timezone.utc) - timedelta(hours=1),
        description="Defaults to the last 1 hour for immediate heat trends"
    ),
    end_time: datetime = Query(
        default_factory=lambda: datetime.now(timezone.utc)
    ),
    db: AsyncSession = Depends(get_db)
) -> AnalyticsHeatmapResponse:
    """
    Aggregates ZONE_DWELL events per zone and normalizes them into a 0.0-1.0 density score
    used by the frontend canvas overlay to render the heatmap.
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="start_time must be strictly before end_time."
        )

    try:
        service = AnalyticsService(db)
        return await service.calculate_heatmap(store_id, start_time, end_time)
    except Exception as e:
        logger.error(f"Failed to calculate heatmap for store {store_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during heatmap aggregation."
        )


@router.get(
    "/{store_id}/anomalies",
    summary="Get Store Anomalies",
    description="Detects dead camera feeds, queue spikes, or sudden conversion drops."
)
async def get_store_anomalies(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Queries the anomaly detection engine heuristics.
    """
    try:
        service = AnalyticsService(db)
        return await service.detect_anomalies(store_id)
    except Exception as e:
        logger.error(f"Failed to detect anomalies for store {store_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during anomaly detection."
        )
