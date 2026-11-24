from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="Cart and Wishlist Service",
    description=(
        "Manage shopping carts and wishlists "
        "with authentication and product verification."
    ),
    version="1.0.0",
)

# Root endpoint
@app.get("/")
def home():
    return {
        "message": "Cart and Wishlist Service is running"
    }

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "cart-service",
    }

# Register routes
app.include_router(router)