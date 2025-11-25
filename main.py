import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from hotel.routes import router as hotel_router
from receptionist.routes import router as receptionist_router
from migrations.seed_rooms import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Runs migrations on startup.
    """
    logger.info("Application startup initiated")
    run_migrations()
    yield
    logger.info("Application shutdown initiated")


app = FastAPI(
    lifespan=lifespan,
    title="Hotel Administration API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(hotel_router)
app.include_router(receptionist_router)


@app.get("/")
async def serve_frontend():
    """Serve the chat frontend at the root URL."""
    logger.info("Serving frontend")
    return FileResponse(str(Path(__file__).parent / "index.html"))
