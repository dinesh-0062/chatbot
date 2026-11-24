
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, chat, conversations

load_dotenv()

app = FastAPI(
    title="Knowledge AI API",
    description="AI-powered document intelligence and RAG API",
    version="1.0.0",
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
