from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .errors.errors import ApiError
from .routes.health import router as health_router
from .routes.dashboard import router as dashboard_router
from .services.redis_service import RedisService

# Load environment variables
load_dotenv()

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Test Redis connection
    try:
        redis_health = RedisService.health_check()
        if redis_health["status"] != "healthy":
            raise Exception(redis_health["message"])
        print("Successfully connected to Redis")
    except Exception as e:
        print(f"Warning: Redis connection failed: {str(e)}")
    
    yield
    
    # Cleanup (if needed)
    print("Shutting down application...")

# Initialize FastAPI app
app = FastAPI(
    title="Report Generation API",
    description="API for report generation with Redis integration",
    version="1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health_router,
    prefix="/report-generation",
    tags=["health"]
)

app.include_router(
    dashboard_router,
    prefix="/report-generation",
    tags=["dashboard"]
)

# Error handlers
@app.exception_handler(ApiError)
async def api_error_exception_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.code,
        content={
            "mssg": exc.description,
            "details": str(exc),
            "version": "1.0"
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        error_detail = {
            "location": error["loc"],
            "message": error["msg"],
            "type": error["type"]
        }
        errors.append(error_detail)

    return JSONResponse(
        status_code=400,
        content={
            "message": "Validation Error",
            "details": errors,
            "version": "1.0"
        },
    )

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "details": str(exc),
            "version": "1.0"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )