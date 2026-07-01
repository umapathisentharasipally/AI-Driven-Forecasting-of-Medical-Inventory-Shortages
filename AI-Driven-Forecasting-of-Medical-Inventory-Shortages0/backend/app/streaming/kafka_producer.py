import json
from typing import Optional

from aiokafka import AIOKafkaProducer
from app.config.settings import settings
from app.streaming.event_schema import KafkaEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KafkaProducerService:
    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=settings.KAFKA_CLIENT_ID,
                value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
                key_serializer=lambda key: key.encode("utf-8") if key else None,
                acks="all",
                enable_idempotence=True,
                retry_backoff_ms=500,
                request_timeout_ms=30000,
            )
            await self._producer.start()
            logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def publish(self, topic: str, event: KafkaEvent) -> None:
        if self._producer is None:
            await self.start()

        await self._producer.send_and_wait(
            topic=topic,
            key=event.entity_id or event.event_id,
            value=event.model_dump(),
        )


kafka_producer = KafkaProducerService()
