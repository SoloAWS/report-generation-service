import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .errors.errors import ApiError
from .routes.health import router as health_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Report Generation API",
    description="API for report generation with Redis integration",
    version="1.0"
)

# Include routers
app.include_router(health_router, prefix="/report-generation")

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