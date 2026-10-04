"""FastAPI application entrypoint.

Run from the `backend` folder:
    uvicorn src.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.models import get_available_models
from src.api.chat_routes import router as chat_router
from src.config import get_settings
from src.database.connection import close_mongo_connection, connect_to_mongo

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Weather & Search Agent API",
    description="LangGraph agent with OpenWeather + Tavily tools and MongoDB chat history.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/")
async def main():
    return {"status": "home page working"}

@app.get("/api/health", tags=["health"])
async def health():
    s = get_settings()
    return {
        "status": "ok",
        "llm_providers": [name for name, _ in get_available_models()],
        "openweather_configured": bool(s.openweather_api_key),
        "tavily_configured": bool(s.tavily_api_key),
    }
