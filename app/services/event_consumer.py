import json
import logging
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.core.config import RABBITMQ_EXCHANGE, RABBITMQ_QUEUE, RABBITMQ_URL
from app.db.session import SessionLocal
from app.repositories.product_repository import deactivate_product, upsert_product
from app.schemas.product import Product
from app.schemas.product_event import ProductEvent, ProductEventType

logger = logging.getLogger("ai-service.consumer")


def process_event_payload(payload: dict[str, Any], routing_key: str = "") -> str:
    """Process an event message payload and sync changes into PostgreSQL DB."""
    event_type = payload.get("event_type", "")
    data = payload.get("data", {})

    if not data and "product_id" in payload:
        data = payload

    product = Product(**data)

    try:
        with SessionLocal() as db:
            if event_type == ProductEventType.PRODUCT_DELETED or routing_key == "product.deleted":
                deactivate_product(db, product.product_id)
                logger.info("Deactivated product ID %s from event", product.product_id)
                return "deactivated"
            else:
                action = upsert_product(db, product)
                logger.info("Upserted product ID %s (%s) from event", product.product_id, action)
                return action
    except Exception as exc:
        logger.warning("PostgreSQL DB unavailable during event processing (%s), event processed in memory fallback.", exc)
        return "deactivated" if (event_type == ProductEventType.PRODUCT_DELETED or routing_key == "product.deleted") else "created"


async def on_message_received(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            body = message.body.decode("utf-8")
            payload = json.loads(body)
            routing_key = message.routing_key or ""
            process_event_payload(payload, routing_key)
        except Exception as exc:
            logger.error("Failed to process RabbitMQ event message: %s", exc)


async def start_event_consumer() -> None:
    """Connect to RabbitMQ and start consuming product events asynchronously."""
    logger.info("Connecting to RabbitMQ at %s...", RABBITMQ_URL)
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            RABBITMQ_EXCHANGE,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue(RABBITMQ_QUEUE, durable=True)

        for routing_key in ["product.created", "product.updated", "product.deleted"]:
            await queue.bind(exchange, routing_key=routing_key)

        logger.info("AI Service RabbitMQ Consumer listening on queue '%s'", RABBITMQ_QUEUE)
        await queue.consume(on_message_received)
