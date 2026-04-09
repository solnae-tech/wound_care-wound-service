from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from db import models
from db.database import engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup complete.")
    yield

app = FastAPI(lifespan=lifespan, title="Wound Care Analytics API", version="1.0.0")
# Adding middleware to resolve CORS issue - Need to update accordingly
# when deployed for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#  Below are the paths excluding for the bearer token check
exclude_paths = [
    r"^/$",
    r"^/docs($|/.*)",
    r"^/health$",
    r"^/redoc($|/.*)",
    r"^/favicon.ico$",
    r"^/openapi.json$",
]


app.include_router(router,prefix="/v1")
