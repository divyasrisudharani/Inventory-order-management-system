import asyncio
import json
import logging
from pathlib import Path

import aio_pika
from dotenv import load_dotenv
import os
from app.database import SessionLocal
from app.models import Notification

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "order_created"

logger = logging.getLogger(__name__)


async def consume_order_events():
    while True:
        try:
            if not RABBITMQ_URL:
                raise ValueError("RABBITMQ_URL is missing")

            connection = await aio_pika.connect_robust(RABBITMQ_URL)

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)

                queue = await channel.declare_queue(
                    QUEUE_NAME,
                    durable=True
                )

                print("Notification Service: RabbitMQ consumer started")

                async with queue.iterator() as messages:
                    async for message in messages:
                        async with message.process():
                            data = json.loads(message.body.decode())

                            db = SessionLocal()
                            try:
                                notification = Notification(
                                    user_id=int(data["user_id"]),
                                    notification_type="ORDER",
                                    title="Order Placed Successfully",
                                    message=(
                                        f"Your order #{data['order_id']} "
                                        "has been placed successfully."
                                    ),
                                    related_id=int(data["order_id"]),
                                )

                                db.add(notification)
                                db.commit()

                                print(
                                    f"Notification saved for order "
                                    f"{data['order_id']}"
                                )
                            except Exception:
                                db.rollback()
                                raise
                            finally:
                                db.close()

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("RabbitMQ consumer error. Retrying in 5 seconds.")
            await asyncio.sleep(5)