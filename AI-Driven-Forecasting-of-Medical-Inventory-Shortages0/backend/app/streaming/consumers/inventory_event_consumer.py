import asyncio
import json

from aiokafka import AIOKafkaConsumer

from app.config.database import connect_db, close_db_connection, get_database
from app.config.settings import settings
from app.realtime.connection_manager import socket_manager
from app.streaming.topics import INVENTORY_EVENTS_TOPIC, ALERT_EVENTS_TOPIC
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_inventory_event(event: dict) -> None:
    db = await get_database()

    await db["event_logs"].insert_one({
        "event_type": event.get("event_type"),
        "entity": event.get("entity"),
        "entity_id": event.get("entity_id"),
        "payload": event.get("payload", {}),
        "created_at": utc_now(),
    })

    await socket_manager.broadcast("inventory", event)
    await socket_manager.broadcast("dashboard", event)

    payload = event.get("payload", {})
    current_stock = payload.get("current_stock")

    if isinstance(current_stock, int) and current_stock <= 10:
        alert = {
            "event_type": "LOW_STOCK_ALERT",
            "entity": "inventory",
            "entity_id": event.get("entity_id"),
            "message": f"Low stock detected for {payload.get('item_name')}",
            "severity": "high",
            "payload": payload,
            "created_at": utc_now(),
        }

        await db["alerts"].insert_one(alert)
        await socket_manager.broadcast("alerts", alert)


async def consume() -> None:
    await connect_db()

    consumer = AIOKafkaConsumer(
        INVENTORY_EVENTS_TOPIC,
        ALERT_EVENTS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    await consumer.start()
    logger.info("Kafka inventory consumer started")

    try:
        async for message in consumer:
            try:
                event = message.value

                if message.topic == INVENTORY_EVENTS_TOPIC:
                    await handle_inventory_event(event)

                await consumer.commit()

            except Exception as exc:
                logger.exception(f"Kafka event processing failed: {exc}")

    finally:
        await consumer.stop()
        await close_db_connection()


if __name__ == "__main__":
    asyncio.run(consume())
