from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import cases, states, commissions


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.info("Application starting up...")
    yield
    logging.info("Application shutting down...")


app = FastAPI(
    title="Lexi Case Tracker API",
    description="API for tracking legal cases from Indian District Consumer Courts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api/v1", tags=["cases"])
app.include_router(states.router, prefix="/api/v1", tags=["states"])
app.include_router(commissions.router, prefix="/api/v1", tags=["commissions"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail, "status_code": exc.status_code}