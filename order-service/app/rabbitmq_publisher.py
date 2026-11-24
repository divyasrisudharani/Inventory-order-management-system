import os
import json
from pathlib import Path

import aio_pika
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "order_created"


async def publish_order_created(event: dict):
    if not RABBITMQ_URL:
        raise ValueError("RABBITMQ_URL is missing")

    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    try:
        channel = await connection.channel()

        queue = await channel.declare_queue(
            QUEUE_NAME,
            durable=True
        )

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(event).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )
    finally:
        await connection.close()