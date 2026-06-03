"""
Purpose: Database Seeder for generating realistic synthetic store analytics data.
Responsibilities:
- Enable pgvector extension.
- Create all database tables from SQLAlchemy models.
- Seed 3 stores with cameras, zones, visitors, and thousands of events.
- Generate realistic temporal patterns (morning rush, afternoon lull, evening peak).

Usage: docker exec -it si_backend_api python -m scripts.seed
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, engine
from src.models import Base
from src.models.event import Event, EventType
from src.models.store import Camera, Store, Zone
from src.models.visitor import Visitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seeder")

# ==========================================
# STORE DEFINITIONS (matching frontend dropdown)
# ==========================================
STORES = [
    {
        "id": uuid.UUID("a1b2c3d4-0001-4000-8000-000000000001"),
        "name": "NYC Flagship",
        "timezone": "America/New_York",
        "cameras": [
            {"name": "Entrance Left",  "rtsp_url": "rtsp://192.168.1.10:554/stream1"},
            {"name": "Entrance Right", "rtsp_url": "rtsp://192.168.1.11:554/stream1"},
            {"name": "Outside Area",   "rtsp_url": "rtsp://192.168.1.12:554/stream1"},
            {"name": "Storage Room",   "rtsp_url": "rtsp://192.168.1.13:554/stream1"},
            {"name": "Billing Counter","rtsp_url": "rtsp://192.168.1.14:554/stream1"},
        ],
        "zones": [
            # ---------------------------------------------------------------------------
            # Store Entrance — bottom 40 % of cam-1 and cam-2 (where people walk in).
            # Polygon is in normalized 0.0–1.0 coordinates (resolution-independent).
            # ---------------------------------------------------------------------------
            {
                "name": "Store Entrance",
                "zone_type": "ENTRY_LINE",
                "polygon": {
                    "camera_ids": ["cam-1", "cam-2"],
                    "points": [
                        {"x": 0.0, "y": 0.60},
                        {"x": 1.0, "y": 0.60},
                        {"x": 1.0, "y": 1.0},
                        {"x": 0.0, "y": 1.0},
                    ],
                },
            },
            # ---------------------------------------------------------------------------
            # Products / browsing area — middle section of cam-1 and cam-2.
            # ---------------------------------------------------------------------------
            {
                "name": "Products Display",
                "zone_type": "DISPLAY",
                "polygon": {
                    "camera_ids": ["cam-1", "cam-2"],
                    "points": [
                        {"x": 0.10, "y": 0.15},
                        {"x": 0.90, "y": 0.15},
                        {"x": 0.90, "y": 0.62},
                        {"x": 0.10, "y": 0.62},
                    ],
                },
            },
            # ---------------------------------------------------------------------------
            # Outside Approach — cam-3 covers the area outside / in front of the store.
            # Full-frame coverage so any detection on cam-3 registers here.
            # ---------------------------------------------------------------------------
            {
                "name": "Outside Approach",
                "zone_type": "AISLE",
                "polygon": {
                    "camera_ids": ["cam-3"],
                    "points": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 1.0, "y": 0.0},
                        {"x": 1.0, "y": 1.0},
                        {"x": 0.0, "y": 1.0},
                    ],
                },
            },
            # ---------------------------------------------------------------------------
            # Storage Room — cam-4 points at the stockroom / storage side of the store.
            # Full-frame coverage.
            # ---------------------------------------------------------------------------
            {
                "name": "Storage Room",
                "zone_type": "AISLE",
                "polygon": {
                    "camera_ids": ["cam-4"],
                    "points": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 1.0, "y": 0.0},
                        {"x": 1.0, "y": 1.0},
                        {"x": 0.0, "y": 1.0},
                    ],
                },
            },
            # ---------------------------------------------------------------------------
            # Billing Counter — cam-5 covers the checkout desk.
            #
            # The operator sits behind the counter with a laptop/computer visible in the
            # upper-centre of the frame.  A customer standing on the OTHER side of the
            # counter (facing the operator) occupies the LOWER portion of the frame
            # (y ≥ 0.45). That lower area is what we designate as the billing queue zone.
            # Anyone whose feet land in this region is treated as "at the billing counter".
            # ---------------------------------------------------------------------------
            {
                "name": "Billing Counter",
                "zone_type": "QUEUE",
                "polygon": {
                    "camera_ids": ["cam-5"],
                    "points": [
                        {"x": 0.10, "y": 0.45},
                        {"x": 0.90, "y": 0.45},
                        {"x": 0.90, "y": 1.0},
                        {"x": 0.10, "y": 1.0},
                    ],
                },
            },
        ],
    },
    {
        "id": uuid.UUID("a1b2c3d4-0002-4000-8000-000000000002"),
        "name": "Store 2",
        "timezone": "America/New_York",
        "cameras": [
            {"name": "Entry 1", "rtsp_url": "rtsp://localhost:$RTSP_PORT/store2-cam1"},
            {"name": "Entry 2", "rtsp_url": "rtsp://localhost:$RTSP_PORT/store2-cam2"},
            {"name": "Zone Area", "rtsp_url": "rtsp://localhost:$RTSP_PORT/store2-cam3"},
            {"name": "Billing Area", "rtsp_url": "rtsp://localhost:$RTSP_PORT/store2-cam4"},
        ],
        "zones": [
            {
                "name": "Entrance Gate 1", 
                "zone_type": "ENTRY_LINE", 
                "polygon": {
                    "camera_ids": ["cam-1"],
                    "points": [{"x": 0.0, "y": 0.5}, {"x": 1.0, "y": 0.5}, {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0}]
                }
            },
            {
                "name": "Entrance Gate 2", 
                "zone_type": "ENTRY_LINE", 
                "polygon": {
                    "camera_ids": ["cam-2"],
                    "points": [{"x": 0.0, "y": 0.5}, {"x": 1.0, "y": 0.5}, {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0}]
                }
            },
            {
                "name": "Browsing Zone", 
                "zone_type": "DISPLAY", 
                "polygon": {
                    "camera_ids": ["cam-3"],
                    "points": [{"x": 0.1, "y": 0.1}, {"x": 0.9, "y": 0.1}, {"x": 0.9, "y": 0.9}, {"x": 0.1, "y": 0.9}]
                }
            },
            {
                "name": "Billing Counter", 
                "zone_type": "QUEUE", 
                "polygon": {
                    "camera_ids": ["cam-4"],
                    "points": [{"x": 0.2, "y": 0.4}, {"x": 0.8, "y": 0.4}, {"x": 0.8, "y": 1.0}, {"x": 0.2, "y": 1.0}]
                }
            },
        ],
    },
    {
        "id": uuid.UUID("a1b2c3d4-0003-4000-8000-000000000003"),
        "name": "London Soho",
        "timezone": "Europe/London",
        "cameras": [
            {"name": "Street Entrance", "rtsp_url": "rtsp://172.16.0.10:554/stream1"},
            {"name": "Main Floor", "rtsp_url": "rtsp://172.16.0.11:554/stream1"},
        ],
        "zones": [
            {"name": "Front Door", "zone_type": "ENTRY_LINE", "polygon": [{"x": 0, "y": 0}, {"x": 120, "y": 0}, {"x": 120, "y": 30}, {"x": 0, "y": 30}]},
            {"name": "New Arrivals", "zone_type": "DISPLAY", "polygon": [{"x": 20, "y": 60}, {"x": 180, "y": 60}, {"x": 180, "y": 200}, {"x": 20, "y": 200}]},
            {"name": "Sale Rack", "zone_type": "DISPLAY", "polygon": [{"x": 200, "y": 60}, {"x": 350, "y": 60}, {"x": 350, "y": 200}, {"x": 200, "y": 200}]},
            {"name": "Payment Queue", "zone_type": "QUEUE", "polygon": [{"x": 200, "y": 250}, {"x": 350, "y": 250}, {"x": 350, "y": 380}, {"x": 200, "y": 380}]},
        ],
    },
]


def generate_hourly_weight(hour: int) -> float:
    """
    Simulates realistic foot traffic patterns throughout the day.
    Morning rush (10-12), lunch peak (12-14), afternoon dip (14-16), evening surge (17-20).
    """
    weights = {
        0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0,
        6: 0.02, 7: 0.05, 8: 0.10, 9: 0.20,
        10: 0.55, 11: 0.70, 12: 0.85, 13: 0.80,
        14: 0.60, 15: 0.55, 16: 0.65, 17: 0.80,
        18: 0.90, 19: 0.75, 20: 0.50, 21: 0.30,
        22: 0.10, 23: 0.02,
    }
    return weights.get(hour, 0.1)


async def seed_database():
    """Main seeder function."""

    # 1. Enable pgvector extension
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("✅ pgvector extension enabled.")

    # 2. Create all tables from our SQLAlchemy models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ All database tables created.")

    # 3. Seed data
    async with AsyncSessionLocal() as session:
        async with session.begin():

            now = datetime.now(timezone.utc)
            twenty_four_hours_ago = now - timedelta(hours=24)

            for store_def in STORES:
                store_id = store_def["id"]

                # --- Create Store ---
                store = Store(
                    id=store_id,
                    name=store_def["name"],
                    timezone=store_def["timezone"],
                )
                session.add(store)
                logger.info(f"  📍 Seeding store: {store_def['name']}")

                # --- Create Cameras ---
                for cam_def in store_def["cameras"]:
                    cam = Camera(
                        store_id=store_id,
                        name=cam_def["name"],
                        rtsp_url=cam_def["rtsp_url"],
                    )
                    session.add(cam)

                # --- Create Zones ---
                zone_ids = []
                queue_zone_ids = []
                display_zone_ids = []
                for zone_def in store_def["zones"]:
                    zone_id = uuid.uuid4()
                    zone = Zone(
                        id=zone_id,
                        store_id=store_id,
                        name=zone_def["name"],
                        zone_type=zone_def["zone_type"],
                        polygon=zone_def["polygon"],
                    )
                    session.add(zone)
                    zone_ids.append(zone_id)
                    if zone_def["zone_type"] == "QUEUE":
                        queue_zone_ids.append(zone_id)
                    elif zone_def["zone_type"] in ("DISPLAY", "AISLE"):
                        display_zone_ids.append(zone_id)
                        
                await session.flush()

                # --- Generate Visitors and Events ---
                # Removed to allow the dashboard to start with 0 metrics and populate strictly from live CCTV data.
                logger.info(f"    👥 Skipped fake event generation for {store_def['name']}")

        logger.info("✅ Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info("Store IDs for API testing:")
        for s in STORES:
            logger.info(f"  {s['name']}: {s['id']}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
