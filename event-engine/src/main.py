import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
import redis.asyncio as redis
from redis.exceptions import ResponseError as RedisResponseError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.event import Event
from src.models.store import Zone
from src.state_machine import EventStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("event-engine")

class EventPublisher:
    def __init__(self, async_session_maker, redis_client):
        self.async_session_maker = async_session_maker
        self.redis_client = redis_client
        self.queue = asyncio.Queue()
        self.worker_task = asyncio.create_task(self._worker())

    def publish(self, payload: dict):
        # Non-blocking publish to queue
        self.queue.put_nowait(payload)

    async def _worker(self):
        while True:
            try:
                payload = await self.queue.get()
                
                # Publish to Redis Pub/Sub for live dashboard
                try:
                    await self.redis_client.publish("live_events", json.dumps(payload))
                except Exception as e:
                    logger.error(f"Error publishing to Redis live_events: {e}")

                # Insert event into postgres
                async with self.async_session_maker() as session:
                    event_time = datetime.fromtimestamp(payload["timestamp"], tz=timezone.utc)
                    db_event = Event(
                        id=uuid.uuid4(),
                        store_id=payload["store_id"],
                        visitor_id=payload.get("visitor_id"),
                        zone_id=payload.get("zone_id"),
                        event_type=payload["event_type"],
                        timestamp=event_time,
                        metadata_payload=payload.get("metadata", {})
                    )
                    session.add(db_event)
                    await session.commit()
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Error persisting event to DB: {e}")

async def main():
    logger.info("Event Engine is starting...")
    
    redis_uri = os.getenv("REDIS_URI", "redis://redis:6379/0")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_SERVER", "postgres")
    db_name = os.getenv("POSTGRES_DB", "store_intelligence")
    
    db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    r = redis.from_url(redis_uri)
    
    publisher = EventPublisher(async_session, r)
    state_machine = EventStateMachine(publisher)
    
    # Load all zones from database to compile Shapely polygons
    logger.info("Loading store zones from database...")
    async with async_session() as session:
        result = await session.execute(select(Zone))
        zones = result.scalars().all()
        
        # Group zones by store_id
        store_zones = {}
        for z in zones:
            if z.store_id not in store_zones:
                store_zones[z.store_id] = []
            store_zones[z.store_id].append({
                "id": str(z.id),
                "name": z.name,
                "zone_type": z.zone_type,
                "polygon": z.polygon
            })
            
        for store_id, z_data in store_zones.items():
            state_machine.load_zones(str(store_id), z_data)

    r = redis.from_url(redis_uri)
    input_stream = "telemetry_resolved"
    group_name = "event_engine_group"
    
    try:
        await r.xgroup_create(input_stream, group_name, id="0", mkstream=True)
        logger.info(f"Created consumer group {group_name} on {input_stream}")
    except RedisResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info("Consumer group already exists.")
        else:
            logger.error(f"Error creating consumer group: {e}")

    logger.info("Event Engine ready. Awaiting telemetry...")
    
    while True:
        try:
            messages = await r.xreadgroup(group_name, "ee_worker_1", {input_stream: ">"}, count=100, block=1000)
            
            for stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    msg = {k.decode('utf-8') if isinstance(k, bytes) else k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in msg_data.items()}
                    
                    try:
                        telemetry = {
                            "store_id": msg["store_id"],
                            "camera_id": msg["camera_id"],
                            "visitor_id": msg["visitor_id"],
                            "bbox": json.loads(msg["bbox"]),
                            "frame_width": int(msg["frame_width"]) if "frame_width" in msg else 1920,
                            "frame_height": int(msg["frame_height"]) if "frame_height" in msg else 1080,
                            "timestamp": float(msg["timestamp"])
                        }
                        
                        state_machine.process_telemetry(telemetry)
                                
                    except Exception as e:
                        logger.error(f"Error processing telemetry {msg_id}: {e}")
                    
                    await r.xack(input_stream, group_name, msg_id)
                    
        except Exception as e:
            logger.error(f"Redis stream error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
