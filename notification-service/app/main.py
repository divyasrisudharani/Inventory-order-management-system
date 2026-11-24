from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router
import asyncio
from contextlib import asynccontextmanager
from app.rabbitmq_consumer import consume_order_events
Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = asyncio.create_task(consume_order_events())
    yield
    consumer_task.cancel()

    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
app = FastAPI(
    title="Notification Service",
    description="Manage order, payment, and inventory notifications.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "message": "Notification Service is running",
        "service": "notification-service",
        "port": 8007,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "notification-service",
    }


app.include_router(router)