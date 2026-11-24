from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Coupon Service",
    description="Manage discount coupons and calculate discounts.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Coupon Service is running",
        "service": "coupon-service",
        "port": 8009,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "coupon-service",
    }


app.include_router(router)