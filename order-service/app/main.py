from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models
from app.routes import router


# Create database tables
Base.metadata.create_all(bind=engine)


# Initialize FastAPI application
app = FastAPI(
    title="Order Management Service",
    description=(
        "Manage customer orders, order items, "
        "order status, and inventory reservations."
    ),
    version="1.0.0",
)

# Root endpoint
@app.get("/")
def home():
    return {
        "message": "Order Management Service is running",
        "service": "order-service",
        "port": 8005,
    }


# Health-check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "order-service",
    }


# Register order routes
app.include_router(router)