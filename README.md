# Pattern TTS Service

**OpenAI-Compatible Text-to-Speech API** using Kokoro TTS v1.0

Fast, high-quality neural TTS with 67 voices across 8 languages. Drop-in replacement for OpenAI's TTS API.

---

## 🎯 Quick Links

- **Swagger UI**: http://localhost:8205/docs (via kubectl port-forward)
- **OpenAPI Spec**: http://localhost:8205/openapi.json
- **Health Check**: http://localhost:8205/health
- **Voices List**: http://localhost:8205/voices
- **Kubernetes Service**: `pattern-tts-service.pattern-agentic.svc.cluster.local`

---

## 🚀 Quick Start

### Local Development

```bash
# Port forward to access service locally
kubectl port-forward -n pattern-agentic svc/pattern-tts-service 8205:80

# Test health endpoint
curl http://localhost:8205/health

# Generate speech (OpenAI-compatible)
curl -X POST http://localhost:8205/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello from Pattern TTS!",
    "voice": "alloy",
    "speed": 1.0
  }' \
  --output speech.mp3
```

### From DLE or Other Services

```python
import httpx

async def generate_speech(text: str, voice: str = "alloy"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://pattern-tts-service.pattern-agentic.svc.cluster.local/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "speed": 1.0
            }
        )
        return response.content  # MP3 audio bytes
```

---

## 📋 Features

- ✅ **OpenAI API Compatible** - Drop-in replacement for `/v1/audio/speech`
- ✅ **67 Voices** - Multiple languages, genders, and styles
- ✅ **Fast Processing** - 6-7 seconds per request (CPU), <1s with GPU
- ✅ **FastAPI** - Modern async Python framework with auto-generated docs
- ✅ **Kubernetes Native** - Helm charts, HPA, health checks
- ✅ **Production Ready** - Non-root, read-only filesystem, resource limits
- ✅ **Persistent Models** - PVC-backed storage, survives pod restarts

---

## 🎙️ Available Voices

### OpenAI-Compatible Voices
Use these with the `/v1/audio/speech` endpoint:

| Voice | Kokoro Equivalent | Description |
|-------|------------------|-------------|
| `alloy` | `af_sky` | Clear, professional female |
| `echo` | `am` | Standard male voice |
| `fable` | `af` | Standard female voice |
| `onyx` | `am_adam` | Deep, authoritative male |
| `nova` | `af_nova` | Female voice |
| `shimmer` | `af_bella` | Female voice |

### Native Kokoro Voices (67 total)
See full list at `/voices` endpoint or [voice_manager.py](src/pattern_tts/services/voice_manager.py)

**Languages**: English (US/British), French, Italian, Portuguese, Japanese, Chinese, Hindi

---

## 🔌 API Endpoints

### OpenAI-Compatible

#### POST `/v1/audio/speech`
Generate speech from text (OpenAI TTS API compatible)

**Request:**
```json
{
  "model": "tts-1",           // or "tts-1-hd", "kokoro"
  "input": "Text to speak",   // Max 4096 characters
  "voice": "alloy",           // OpenAI or Kokoro voice ID
  "speed": 1.0                // 0.25 to 4.0
}
```

**Response:** Audio file (MP3, 24kHz mono, 64kbps)

**Curl Example:**
```bash
curl -X POST http://localhost:8205/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "The Pattern TTS Service is now operational!",
    "voice": "onyx",
    "speed": 1.0
  }' \
  --output announcement.mp3
```

#### GET `/v1/models`
List available TTS models

**Response:**
```json
{
  "models": [
    {"id": "tts-1", "description": "Standard quality TTS"},
    {"id": "tts-1-hd", "description": "High definition TTS"},
    {"id": "kokoro", "description": "Native Kokoro model"}
  ]
}
```

#### GET `/v1/audio/voices`
List all available voices with metadata

**Response:**
```json
{
  "voices": [
    {
      "id": "alloy",
      "name": "Alloy",
      "language": "en-US",
      "gender": "female",
      "kokoro_voice": "af_sky"
    }
  ]
}
```

---

### Service Endpoints

#### GET `/health`
Health check for liveness/readiness probes

**Response:**
```json
{
  "status": "healthy",
  "service": "pattern-tts-service",
  "version": "1.0.0",
  "port": 8205,
  "timestamp": "2026-01-16T03:10:21.513016"
}
```

#### GET `/voices`
List native Kokoro voices with detailed metadata

---

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_ENVIRONMENT` | `dev` | Environment (dev/staging/prod) |
| `TTS_LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `TTS_PORT` | `8205` | Service port |
| `TTS_HOST` | `0.0.0.0` | Bind host |
| `TTS_MODEL_PATH` | `/models/kokoro-v1.0` | Path to model files |
| `USE_GPU` | `false` | Enable GPU acceleration |
| `TTS_MAX_TEXT_LENGTH` | `4096` | Max characters per request |
| `TTS_TEMP_DIR` | `/tmp/tts` | Temporary file directory |

### Kubernetes Resources

**Current Deployment** (values-dev.yaml):
```yaml
replicas: 2-8 (HPA auto-scaling)
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 4Gi
```

**PVC**: 20Gi gp3-xfs (models + voice files = 346MB)

---

## 🚢 Deployment

### Prerequisites
- Kubernetes cluster with kubectl access
- Helm 3+
- AWS ECR access (for pulling images)
- PVC with Kokoro models uploaded

### Deploy to Kubernetes

```bash
# Navigate to repo
cd /home/jeremy/pattern_agentic/pattern-tts-service

# Install with Helm
helm install pattern-tts helm/pattern-tts \
  -f helm/pattern-tts/values-dev.yaml \
  -n pattern-agentic

# Check deployment status
kubectl get pods -n pattern-agentic | grep pattern-tts

# View logs
kubectl logs -n pattern-agentic -l app=pattern-tts-service --tail=100

# Port forward for local access
kubectl port-forward -n pattern-agentic svc/pattern-tts-service 8205:80
```

### Upgrade Deployment

```bash
# Pull latest image and upgrade
helm upgrade pattern-tts helm/pattern-tts \
  -f helm/pattern-tts/values-dev.yaml \
  -n pattern-agentic
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment pattern-tts -n pattern-agentic --replicas=3

# Scale to 0 (save resources when not in use)
kubectl scale deployment pattern-tts -n pattern-agentic --replicas=0

# Scale back up
kubectl scale deployment pattern-tts -n pattern-agentic --replicas=2

# Check HPA status
kubectl get hpa -n pattern-agentic pattern-tts
```

---

## 📊 Monitoring

### Health Checks

```bash
# Health endpoint
curl http://localhost:8205/health

# Kubernetes readiness
kubectl get pods -n pattern-agentic -l app=pattern-tts-service

# Check HPA metrics
kubectl get hpa -n pattern-agentic pattern-tts
```

### Resource Usage

```bash
# Pod resource consumption
kubectl top pods -n pattern-agentic | grep pattern-tts

# PVC usage
kubectl exec -n pattern-agentic pvc-uploader -- df -h /models
```

### Logs

```bash
# Real-time logs (all pods)
kubectl logs -n pattern-agentic -l app=pattern-tts-service -f

# Specific pod
kubectl logs -n pattern-agentic pattern-tts-<pod-id> --tail=50

# Previous crashed pod
kubectl logs -n pattern-agentic pattern-tts-<pod-id> --previous
```

---

## 🧪 Testing

### Manual Testing

```bash
# Port forward
kubectl port-forward -n pattern-agentic svc/pattern-tts-service 8205:80 &

# Test health
curl http://localhost:8205/health | python -m json.tool

# Generate speech with different voices
for voice in alloy echo fable onyx nova shimmer; do
  curl -X POST http://localhost:8205/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"tts-1\",\"input\":\"Testing voice $voice\",\"voice\":\"$voice\"}" \
    --output "test_${voice}.mp3"
done

# Verify audio files
file test_*.mp3
```

### Load Testing

```bash
# Concurrent requests
seq 1 10 | xargs -P 10 -I {} curl -X POST http://localhost:8205/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Load test request {}","voice":"alloy"}' \
  --output "load_test_{}.mp3"
```

---

## 🐛 Troubleshooting

### Pod CrashLoopBackOff

**Symptom**: Pods restart repeatedly with `FileNotFoundError: /models/af_sky.pt`

**Cause**: PVC mount race condition during startup

**Fix**:
```bash
# Increase readiness probe delay
kubectl patch deployment pattern-tts -n pattern-agentic -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"tts-service","readinessProbe":{"initialDelaySeconds":30}}]}}}}'
```

### High Memory Usage

**Symptom**: Pods OOMKilled or memory >80%

**Solution**: Increase memory limits in values.yaml:
```yaml
resources:
  limits:
    memory: 6Gi  # Increase from 4Gi
```

### Slow Response Times

**Symptom**: Requests taking >10 seconds

**Diagnosis**:
1. Check CPU throttling: `kubectl top pods -n pattern-agentic`
2. Check concurrent requests: Review logs for queue depth
3. Consider GPU deployment for <1s latency

---

## 📚 Additional Documentation

- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup and contribution guide
- Work Orders: `.mr_ai/agents/work_orders/WO-015-*`

---

## 🏆 Quality Gates (Agent 6 Validation)

**Status**: ✅ **CONDITIONAL PASS** (3/4 gates pass, 1 with warnings)

| Gate | Status | Notes |
|------|--------|-------|
| **Functional Correctness** | ✅ PASS | All endpoints operational |
| **Integration** | ✅ PASS | OpenAI API compatible |
| **Performance** | ✅ PASS | 6-7s/request (CPU), acceptable for MVP |
| **Stability** | ⚠️ PASS | Startup race condition (monitored) |

---

**Version**: 1.0.3
**Last Updated**: 2026-01-16
**Maintainer**: Pattern Agentic Team
**Port**: 8205 (reserved in PORT_RESERVATIONS.md)
