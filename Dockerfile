# Pattern TTS Service - Production Dockerfile
# Multi-stage build for optimized image size
# Security: Non-root user, read-only filesystem, minimal attack surface

# ============================================================================
# Stage 1: Builder - Install dependencies and download models
# ============================================================================
FROM python:3.11-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    espeak-ng \
    libsndfile1 \
    pkg-config \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavdevice-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml ./

# Install uv and dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Download Kokoro model and voice packs
# This happens during build time to avoid runtime downloads
RUN python -c "from kokoro import generate; generate('test', voice='af', speed=1.0)" || true

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (UID 1000, GID 1000)
RUN groupadd -g 1000 ttsuser && \
    useradd -m -u 1000 -g 1000 -s /bin/bash ttsuser

# Create necessary directories with proper permissions
RUN mkdir -p /app /tmp/tts /models && \
    chown -R ttsuser:ttsuser /app /tmp/tts /models

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Kokoro models from builder (cache location)
COPY --from=builder /root/.cache /home/ttsuser/.cache
RUN chown -R ttsuser:ttsuser /home/ttsuser/.cache

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=ttsuser:ttsuser src/ ./src/
COPY --chown=ttsuser:ttsuser pyproject.toml ./

# Switch to non-root user
USER ttsuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TTS_PORT=8205 \
    TTS_HOST=0.0.0.0 \
    TTS_LOG_LEVEL=INFO \
    TTS_TEMP_DIR=/tmp/tts \
    USE_GPU=false

# Expose port
EXPOSE 8205

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8205/health').raise_for_status()" || exit 1

# Run as non-root with read-only root filesystem
# CMD runs with SecurityContext: readOnlyRootFilesystem=true in Kubernetes
CMD ["uvicorn", "src.pattern_tts.api.main:app", "--host", "0.0.0.0", "--port", "8205", "--workers", "1"]
