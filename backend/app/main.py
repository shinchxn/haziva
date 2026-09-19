from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.habitations import router as habitation_router
from backend.app.api.relocation import router as relocation_router
from backend.app.api.risk import router as risk_router
from backend.app.api.system import router as system_router
from backend.app.core.config import settings
from backend.app.core.error_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)


app = FastAPI(
    title="Haziva Risk & Relocation API",
    description="API layer for habitation-level risk assessment and relocation planning.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(habitation_router)
app.include_router(risk_router)
app.include_router(relocation_router)
app.include_router(system_router)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/")
def read_root():
    return {"message": "Haziva backend API is running."}
