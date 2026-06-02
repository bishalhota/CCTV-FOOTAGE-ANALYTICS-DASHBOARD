import logging
import uuid
from typing import List
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.event import Event, EventType
from src.models.visitor import Visitor
from src.models.transaction import Transaction
from src.models.daily_store_metric import DailyStoreMetric
from fastapi.responses import StreamingResponse
import redis.asyncio as redis
import os
import asyncio
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

class DashboardMetricsResponse(BaseModel):
    footfall: int
    uniqueVisitors: int
    transactions: int
    gmv: float
    conversionRate: float
    averageBasketValue: float
    total_exits: int = 0
    active_visitor_count: int = 0

class DailyTrendResponse(BaseModel):
    metric_date: date
    footfall: int
    unique_visitors: int
    transactions: int
    gmv: float
    conversion_rate: float
    average_basket_value: float


@router.get("/store/{store_id}", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Footfall (Total Entries)
        stmt_footfall = select(func.count(Event.id)).where(
            Event.store_id == store_id,
            Event.event_type == EventType.ENTRY
        )
        footfall_res = await db.execute(stmt_footfall)
        footfall = footfall_res.scalar() or 0

        # Unique Visitors
        stmt_unique = select(func.count(distinct(Event.visitor_id))).where(
            Event.store_id == store_id,
            Event.event_type == EventType.ENTRY
        )
        unique_res = await db.execute(stmt_unique)
        unique_visitors = unique_res.scalar() or 0

        # Transactions & GMV
        stmt_tx = select(
            func.count(Transaction.id).label("tx_count"),
            func.sum(Transaction.gmv).label("total_gmv")
        ).where(
            Transaction.store_id == store_id
        )
        tx_res = await db.execute(stmt_tx)
        tx_row = tx_res.first()

        transactions = tx_row.tx_count if tx_row and tx_row.tx_count else 0
        gmv = float(tx_row.total_gmv) if tx_row and tx_row.total_gmv else 0.0

        conversion_rate = 0.0
        if unique_visitors > 0:
            conversion_rate = (transactions / unique_visitors) * 100.0

        average_basket_value = 0.0
        if transactions > 0:
            average_basket_value = gmv / transactions

        # Total Exits
        stmt_exits = select(func.count(Event.id)).where(
            Event.store_id == store_id,
            Event.event_type == EventType.EXIT
        )
        exits_res = await db.execute(stmt_exits)
        total_exits = exits_res.scalar() or 0

        # Active visitor count: entries - exits (people currently in store)
        active_visitor_count = max(0, footfall - total_exits)

        return DashboardMetricsResponse(
            footfall=footfall,
            uniqueVisitors=unique_visitors,
            transactions=transactions,
            gmv=gmv,
            conversionRate=round(conversion_rate, 1),
            averageBasketValue=round(average_basket_value, 2),
            total_exits=total_exits,
            active_visitor_count=active_visitor_count
        )

    except Exception as e:
        logger.error(f"Failed to fetch dashboard metrics for store {store_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error fetching dashboard metrics"
        )


@router.get("/store/{store_id}/trend", response_model=List[DailyTrendResponse])
async def get_dashboard_trend(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(DailyStoreMetric).where(
            DailyStoreMetric.store_id == store_id
        ).order_by(DailyStoreMetric.metric_date.asc())
        
        result = await db.execute(stmt)
        metrics = result.scalars().all()

        return [
            DailyTrendResponse(
                metric_date=m.metric_date,
                footfall=m.footfall,
                unique_visitors=m.unique_visitors,
                transactions=m.transactions,
                gmv=float(m.gmv),
                conversion_rate=float(m.conversion_rate),
                average_basket_value=float(m.average_basket_value)
            ) for m in metrics
        ]
    except Exception as e:
        logger.error(f"Failed to fetch trend for store {store_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error fetching trend metrics"
        )


@router.get("/store/{store_id}/stream")
async def stream_live_dashboard(store_id: uuid.UUID):
    """
    SSE Endpoint for real-time bounding boxes and physical events.
    """
    redis_uri = os.getenv("REDIS_URI", "redis://redis:6379/0")
    r = redis.from_url(redis_uri)

    async def event_generator():
        pubsub = r.pubsub()
        await pubsub.subscribe("live_events", "live_telemetry", "pipeline_status")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    channel = message["channel"].decode("utf-8")
                    data = message["data"].decode("utf-8")
                    
                    parsed_data = json.loads(data)
                    # Filter by store_id
                    if str(parsed_data.get("store_id")) != str(store_id):
                        continue
                    
                    if channel == "live_telemetry":
                        event_type = "telemetry"
                    elif channel == "pipeline_status":
                        event_type = "pipeline_status"
                    else:
                        event_type = "domain_event"
                    
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    # Keep-alive
                    yield ": keep-alive\n\n"
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info("Client disconnected from SSE stream")
        finally:
            await pubsub.unsubscribe()
            await r.aclose()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
