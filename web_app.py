"""FastAPI application entry point for AeroDrift."""

from fastapi import FastAPI

from api import router


app = FastAPI(
    title="AeroDrift API",
    description="Read and scan API for the local AeroDrift topology analyzer.",
    version="1.0.0",
)
app.include_router(router)