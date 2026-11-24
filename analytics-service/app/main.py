from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Analytics Service",
    description="Generate sales summaries and product performance reports.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Analytics Service is running",
        "service": "analytics-service",
        "port": 8011,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "analytics-service",
    }


app.include_router(router)