import os
import aio_pika
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL")


async def connect_rabbitmq():
    if not RABBITMQ_URL:
        raise ValueError("RABBITMQ_URL is missing from the .env file")

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    return connection


async def publish_message(queue_name: str, message: dict):
    connection = await connect_rabbitmq()

    try:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=__import__("json").dumps(message).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )
    finally:
        await connection.close()