from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1 import cases, states, commissions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application starting up...")
    yield
    logging.info("Application shutting down...")


app = FastAPI(
    title="Lexi Case Tracker API",
    description="API for tracking legal cases from Indian District Consumer Courts (DCDRC) - Real Data Integration",
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


@app.get("/")
async def root():
    return {
        "message": "Lexi Case Tracker API - Real Data Integration",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "Real Mode - Connecting to e-Jagriti portal",
        "authentication": "Required - Set JAGRITI_MOBILE and JAGRITI_PASSWORD in .env",
        "setup_instructions": [
            "1. Create .env file with JAGRITI_MOBILE=your_mobile_number",
            "2. Add JAGRITI_PASSWORD=your_password",
            "3. Install playwright: playwright install chromium",
            "4. For headless mode: USE_HEADLESS_BROWSER=true"
        ]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "mode": "real_integration",
        "jagriti_portal": "e-jagriti.gov.in",
        "authentication_configured": bool(settings.JAGRITI_MOBILE and settings.JAGRITI_PASSWORD)
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)