
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, chat, conversations, sources

load_dotenv()


@asynccontextmanager
async def lifespan(application: FastAPI):
    if os.getenv("INITIALIZE_DATABASE", "true").lower() in ("1", "true", "yes"):
        from app.init_db import initialize_database
        initialize_database()
    yield


app = FastAPI(
    title="Knowledge AI API",
    description="AI-powered document intelligence and RAG API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS CONFIGURATION

origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*-5173\.app\.github\.dev",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API ROUTERS

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(sources.router)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Knowledge AI API is running",
    }


@app.get("/health")
def health_check():
    return {
        "success": True,
        "status": "healthy",
        "service": "Knowledge AI",
    }
