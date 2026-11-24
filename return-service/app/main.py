from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Return and Refund Service",
    description="Manage product return requests and refund statuses.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Return and Refund Service is running",
        "service": "return-refund-service",
        "port": 8010,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "return-refund-service",
    }


app.include_router(router)