import asyncio
from rabbitmq_client import connect_rabbitmq


async def main():
    connection = await connect_rabbitmq()
    print("RabbitMQ connected successfully!")

    await connection.close()


if __name__ == "__main__":
    asyncio.run(main())