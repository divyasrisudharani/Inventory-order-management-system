from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Review Service",
    description="Manage product ratings and customer reviews.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Review Service is running",
        "service": "review-service",
        "port": 8008,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "review-service",
    }


app.include_router(router)