# Pattern TTS Service

**OpenAI-Compatible Text-to-Speech API using Kokoro TTS**

**Port**: 8205
**Status**: 🚧 WO-015 Phase 1 - In Development
**Model**: Kokoro TTS v1.0

---

## Overview

Pattern TTS Service provides high-quality text-to-speech synthesis using the Kokoro TTS model. The service exposes an OpenAI-compatible API endpoint, making it a drop-in replacement for OpenAI's TTS API.

**Key Features**:
- ✅ OpenAI-compatible API (`/v1/audio/speech`)
- ✅ Multiple voice options
- ✅ Streaming and file-based output
- ✅ CPU-optimized inference
- ✅ FastAPI with automatic OpenAPI documentation
- ✅ Production-ready (non-root, resource limits, health checks)

---

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn src.pattern_tts.api.main:app --host 0.0.0.0 --port 8205

# Test endpoint
curl http://localhost:8205/health
```

### Docker

```bash
# Build
docker build -t pattern-tts-service:latest -f docker/Dockerfile .

# Run
docker run -p 8205:8205 pattern-tts-service:latest
```

### Kubernetes (Helm)

```bash
# Deploy to dev
helm install pattern-tts helm/pattern-tts -f helm/pattern-tts/values-dev.yaml

# Deploy to prod
helm install pattern-tts helm/pattern-tts -f helm/pattern-tts/values-prod.yaml
```

---

## API Endpoints

### Health Check
```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "pattern-tts-service",
  "version": "1.0.0",
  "model": "kokoro-v1.0",
  "port": 8205
}
```

### Create Speech (OpenAI-Compatible)
```bash
POST /v1/audio/speech
```

**Request**:
```json
{
  "model": "tts-1",
  "input": "Hello, this is Pattern TTS speaking!",
  "voice": "af",
  "response_format": "mp3",
  "speed": 1.0
}
```

**Response**: Audio file (mp3/wav/opus/flac)

**Example**:
```bash
curl -X POST http://localhost:8205/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Welcome to Pattern Agentic",
    "voice": "af"
  }' \
  --output speech.mp3
```

---

## Available Voices

- `af` - Default female voice
- `am` - Default male voice
- Additional voices available (see `/docs` for full list)

---

## Configuration

### Environment Variables

```bash
# Service
TTS_PORT=8205
TTS_HOST=0.0.0.0
TTS_LOG_LEVEL=INFO

# Model
TTS_MODEL_PATH=/models/kokoro-v1.0
USE_GPU=false

# Processing
TTS_MAX_TEXT_LENGTH=5000
TTS_TEMP_DIR=/tmp/tts
```

### Configuration File
See `config/service.yaml` for detailed configuration options.

---

## Development

### Run Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v
```

### Linting

```bash
ruff check src/
black src/
```

---

## Deployment

### AWS EKS (Production)

**Namespace**: `pattern-agentic`
**Service**: `pattern-tts-service`
**Port**: 8205 (internal ClusterIP)

**Access**:
```bash
# Port-forward (development)
kubectl port-forward -n pattern-agentic svc/pattern-tts-service 8205:80

# Via DLE v4 API Gateway (production)
curl http://localhost:8106/audio-proxy/tts
```

---

## Migration from Legacy

**Old**: Kokoro TTS Docker container on port 8880
**New**: Pattern TTS Service on port 8205

**Migration Path**:
1. Phase 1: Deploy to EKS, validate performance
2. Phase 2: A/B testing (10% → 100%)
3. Phase 3: Decommission port 8880 container

---

## Performance

**Expected Metrics** (Target):
- P95 Latency: <500ms for 100-word text
- Throughput: 50+ requests/second
- Success Rate: >99%

---

## Documentation

- **Swagger UI**: http://localhost:8205/docs
- **ReDoc**: http://localhost:8205/redoc
- **OpenAPI Spec**: http://localhost:8205/openapi.json

---

## Support

**Questions**: Ask H200 First Mate or Captain Jeremy
**Issues**: Report in work order system

---

## Work Orders

- **WO-015 Phase 1**: Deployment to AWS EKS + validation
- **WO-015 Phase 2**: A/B testing integration with DLE v4
- **WO-015 Phase 3**: 100% cutover + port 8880 decommission

---

**Never Fade to Black** 🏴‍☠️
