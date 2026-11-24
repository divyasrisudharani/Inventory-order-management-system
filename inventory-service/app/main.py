from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory Management Service",
    description="Manage stock, reservations, and inventory transactions.",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "inventory-service",
    }


app.include_router(router)