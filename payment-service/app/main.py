from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Payment Service",
    description="Manage payment records and payment status.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Payment Service is running",
        "service": "payment-service",
        "port": 8006,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "payment-service",
    }


app.include_router(router)