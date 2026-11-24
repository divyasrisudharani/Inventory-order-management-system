from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models
from app.routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize tables for local development.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Inventory Management - Authentication Service",
    description=(
        "Authentication microservice providing registration, "
        "login, JWT access tokens, refresh tokens, and RBAC."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Development configuration. Restrict origins appropriately in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Authentication Service",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "service": "Authentication Service",
        "status": "healthy",
    }