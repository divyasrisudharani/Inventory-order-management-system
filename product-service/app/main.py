from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router as product_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Inventory Management - Product Service",
    description="Product catalog management microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(product_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Product Catalog Service",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "service": "Product Catalog Service",
        "status": "healthy",
    }