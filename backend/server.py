"""VideoForge AI — modular FastAPI app.

The legacy 1700-line server.py has been split into routers under
backend/routers/* and shared helpers under backend/core/*.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.config import CORS_ORIGINS
from core.db import close_db
from core.migrations import migrate_base64_to_fs
from routers import (
    agent, analytics, auth, billing, calendar, media, pipeline,
    projects, templates, trends, youtube,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: migrate any legacy base64 blobs out of Mongo (idempotent).
    try:
        await migrate_base64_to_fs()
    except Exception as e:
        logging.warning(f"startup migration skipped: {e}")
    yield
    await close_db()


app = FastAPI(title="VideoForge AI", lifespan=lifespan)

api_router = APIRouter(prefix="/api")

# Mount feature routers
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(pipeline.router)
api_router.include_router(agent.router)
api_router.include_router(billing.router)
api_router.include_router(youtube.router)
api_router.include_router(media.router)
api_router.include_router(trends.router)
api_router.include_router(templates.router)
api_router.include_router(calendar.router)
api_router.include_router(analytics.router)


@api_router.get("/")
async def root():
    return {"service": "VideoForge AI", "status": "ok", "version": "stage2-modular"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
