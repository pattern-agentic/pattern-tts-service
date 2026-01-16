"""
Pattern TTS Service - FastAPI Application
OpenAI-compatible Text-to-Speech API using Kokoro TTS
"""

import sys
from contextlib import asynccontextmanager
from datetime import datetime

import torch
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from ..core.config import settings


def setup_logger():
    """Configure loguru logger with custom formatting"""
    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "format": "<fg #2E8B57>{time:HH:mm:ss}</fg #2E8B57> | "
                "{level: <8} | "
                "<fg #4169E1>{module}:{line}</fg #4169E1> | "
                "{message}",
                "colorize": True,
                "level": settings.log_level,
            },
        ],
    }
    logger.remove()
    logger.configure(**config)
    logger.level("ERROR", color="<red>")


# Configure logger
setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model initialization"""
    from ..services.model_manager import ModelManager
    from ..services.voice_manager import VoiceManager

    logger.info("🚀 Initializing Pattern TTS Service")

    try:
        # Initialize managers
        model_manager = ModelManager()
        voice_manager = VoiceManager()

        # Initialize model with warmup
        device, model_name, voice_count = await model_manager.initialize_with_warmup(
            voice_manager
        )

        # Store in app state
        app.state.model_manager = model_manager
        app.state.voice_manager = voice_manager

    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise

    boundary = "=" * 60
    startup_msg = f"""
{boundary}
    {settings.app_name} v{settings.app_version}
    Model: {model_name}
    Device: {device}
{boundary}
"""
    if device == "cuda":
        startup_msg += f"\nCUDA: {torch.cuda.is_available()}"
        if torch.cuda.is_available():
            startup_msg += f"\nGPU: {torch.cuda.get_device_name(0)}"
    startup_msg += f"\nVoices: {voice_count} voice packs loaded"
    startup_msg += f"\n{boundary}\n"

    logger.info(startup_msg)

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Pattern TTS Service")


# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.app_version,
    lifespan=lifespan,
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check - verifies model is loaded"""
    if not hasattr(app.state, "model_manager"):
        return {"status": "not_ready", "reason": "model_manager not initialized"}

    if not hasattr(app.state, "voice_manager"):
        return {"status": "not_ready", "reason": "voice_manager not initialized"}

    return {
        "status": "ready",
        "service": settings.app_name,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Include routers
from .routers.openai_compatible import router as openai_router
app.include_router(openai_router)


def main():
    uvicorn.run(
        "pattern_tts.api.main:app",
        host="0.0.0.0",
        port=8205,
        reload=False,
    )


if __name__ == "__main__":
    main()
