"""FastAPI application entry point for AeroDrift."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api import router


BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "templates" / "dashboard.html"

app = FastAPI(
    title="AeroDrift API",
    description="Read and scan API for the local AeroDrift topology analyzer.",
    version="1.0.0",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    """Serve the browser dashboard shell; data is loaded from the API."""
    return TEMPLATE_PATH.read_text(encoding="utf-8")