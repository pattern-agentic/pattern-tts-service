# Pattern TTS Service - Development Guide

Complete development setup and workflow for contributors.

---

## 🎯 Quick Reference

**Service URLs** (via port-forward):
- Swagger UI: http://localhost:8205/docs
- ReDoc: http://localhost:8205/redoc
- Health: http://localhost:8205/health
- Voices: http://localhost:8205/voices

**Key Files**:
- `src/pattern_tts/api/main.py` - FastAPI app + lifespan
- `src/pattern_tts/api/routers/openai_compatible.py` - OpenAI endpoints
- `src/pattern_tts/services/model_manager.py` - Kokoro model wrapper
- `src/pattern_tts/services/voice_manager.py` - Voice metadata + validation
- `helm/pattern-tts/values-dev.yaml` - Kubernetes dev config

---

## 🚀 Development Setup

### 1. Clone Repository

```bash
cd /home/jeremy/pattern_agentic
git clone <repo-url> pattern-tts-service
cd pattern-tts-service
```

### 2. Install Dependencies

**Python 3.11+ required**

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### 3. Download Models (Local Dev)

```bash
# Create models directory
mkdir -p /tmp/pattern-tts-models

# Extract from Kubernetes PVC (if deployed)
kubectl exec -n pattern-agentic pvc-uploader -- tar -czf - /models | \
  tar -xzf - -C /tmp/pattern-tts-models --strip-components=1

# Or extract from kokoro-tts container
docker cp kokoro-tts:/app/api/src/models/v1_0/ /tmp/pattern-tts-models/

# Verify files
ls -lh /tmp/pattern-tts-models/
# Should see: kokoro-v1_0.pth (313MB), config.json (2.3KB), 67x *.pt files (~511KB each)
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your settings
cat > .env << 'EOF'
TTS_ENVIRONMENT=dev
TTS_LOG_LEVEL=DEBUG
TTS_PORT=8205
TTS_HOST=0.0.0.0
TTS_MODEL_PATH=/tmp/pattern-tts-models/kokoro-v1_0.pth
USE_GPU=false
TTS_MAX_TEXT_LENGTH=4096
TTS_TEMP_DIR=/tmp/tts
EOF
```

### 5. Run Service Locally

```bash
# Activate venv
source .venv/bin/activate

# Run with uvicorn
uvicorn src.pattern_tts.api.main:app \
  --host 0.0.0.0 \
  --port 8205 \
  --reload

# Service starts at http://localhost:8205
# Swagger UI: http://localhost:8205/docs
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit -v

# Run specific test file
pytest tests/unit/test_voice_manager.py -v

# Run with coverage
pytest tests/unit --cov=src/pattern_tts --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Integration Tests

```bash
# Requires service running locally
pytest tests/integration -v

# Test specific endpoint
pytest tests/integration/test_openai_api.py::test_speech_generation -v
```

### End-to-End Tests

```bash
# Requires Kubernetes deployment
export TTS_SERVICE_URL="http://localhost:8205"

pytest tests/e2e -v
```

### Manual Testing Script

```bash
#!/bin/bash
# test_tts_service.sh

# Port forward if testing K8s deployment
kubectl port-forward -n pattern-agentic svc/pattern-tts-service 8205:80 &
PF_PID=$!
sleep 2

# Test health
echo "Testing health endpoint..."
curl -s http://localhost:8205/health | python3 -m json.tool

# Test voices list
echo -e "\nTesting voices endpoint..."
curl -s http://localhost:8205/voices | python3 -m json.tool | head -30

# Test speech generation
echo -e "\nGenerating speech..."
curl -X POST http://localhost:8205/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Pattern TTS Service validation test",
    "voice": "alloy",
    "speed": 1.0
  }' \
  --output /tmp/test-speech.mp3

# Verify audio file
echo -e "\nVerifying audio file..."
file /tmp/test-speech.mp3
ls -lh /tmp/test-speech.mp3

# Cleanup
kill $PF_PID 2>/dev/null
echo -e "\nTest complete!"
```

---

## 🐳 Docker Development

### Build Image

```bash
# Build for local testing
docker build -t pattern-tts-service:dev \
  -f docker/Dockerfile .

# Build with BuildKit (faster)
DOCKER_BUILDKIT=1 docker build -t pattern-tts-service:dev \
  -f docker/Dockerfile .
```

### Run Container

```bash
# Run with local models
docker run -d \
  --name pattern-tts-dev \
  -p 8205:8205 \
  -v /tmp/pattern-tts-models:/models:ro \
  -e TTS_LOG_LEVEL=DEBUG \
  pattern-tts-service:dev

# View logs
docker logs -f pattern-tts-dev

# Test
curl http://localhost:8205/health

# Stop and remove
docker stop pattern-tts-dev
docker rm pattern-tts-dev
```

### Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 --profile pattern-dev | \
  docker login --username AWS --password-stdin \
  085016484061.dkr.ecr.us-west-2.amazonaws.com

# Tag image
docker tag pattern-tts-service:dev \
  085016484061.dkr.ecr.us-west-2.amazonaws.com/pattern-tts-service:v1.0.3

# Push
docker push 085016484061.dkr.ecr.us-west-2.amazonaws.com/pattern-tts-service:v1.0.3
```

---

## ☸️ Kubernetes Development

### Deploy to Dev Environment

```bash
# Navigate to repo
cd /home/jeremy/pattern_agentic/pattern-tts-service

# Install with Helm
helm install pattern-tts helm/pattern-tts \
  -f helm/pattern-tts/values-dev.yaml \
  -n pattern-agentic

# Or upgrade if already installed
helm upgrade pattern-tts helm/pattern-tts \
  -f helm/pattern-tts/values-dev.yaml \
  -n pattern-agentic
```

### Access Service

```bash
# Port forward for local access
kubectl port-forward -n pattern-agentic svc/pattern-tts-service 8205:80

# Or use temporary pod for testing
kubectl run -it --rm --restart=Never \
  --image=curlimages/curl:latest \
  curl-test -- sh

# From inside pod:
curl http://pattern-tts-service.pattern-agentic.svc.cluster.local/health
```

### Debug Pods

```bash
# Get pod status
kubectl get pods -n pattern-agentic | grep pattern-tts

# View logs (all pods)
kubectl logs -n pattern-agentic -l app=pattern-tts-service --tail=100 -f

# View logs (specific pod)
kubectl logs -n pattern-agentic pattern-tts-<pod-id> --tail=200

# Exec into pod
kubectl exec -it -n pattern-agentic pattern-tts-<pod-id> -- sh

# Describe pod (for events)
kubectl describe pod -n pattern-agentic pattern-tts-<pod-id>

# Check resource usage
kubectl top pod -n pattern-agentic | grep pattern-tts
```

### Check HPA

```bash
# Get HPA status
kubectl get hpa -n pattern-agentic pattern-tts

# Watch HPA (real-time)
kubectl get hpa -n pattern-agentic pattern-tts -w

# Describe HPA (events + metrics)
kubectl describe hpa -n pattern-agentic pattern-tts
```

### PVC Management

```bash
# Check PVC status
kubectl get pvc -n pattern-agentic pattern-tts-models

# Upload models to PVC
kubectl apply -f kubernetes/pods/pvc-uploader.yaml

kubectl cp /tmp/pattern-tts-models/kokoro-v1_0.pth \
  pattern-agentic/pvc-uploader:/models/

kubectl cp /tmp/pattern-tts-models/config.json \
  pattern-agentic/pvc-uploader:/models/

# Upload voice files
cd /tmp/pattern-tts-models
for f in *.pt; do
  kubectl cp "$f" pattern-agentic/pvc-uploader:/models/
done

# Verify upload
kubectl exec -n pattern-agentic pvc-uploader -- ls -lh /models/
kubectl exec -n pattern-agentic pvc-uploader -- sh -c 'ls -1 /models/*.pt | wc -l'
# Should return 67
```

---

## 🔧 Troubleshooting

### Service Won't Start

**Check logs**:
```bash
kubectl logs -n pattern-agentic pattern-tts-<pod-id> --tail=50
```

**Common issues**:
1. Models not found: Verify PVC mounted and files exist
2. Port already in use: Check for conflicting services
3. OOM: Increase memory limits in values.yaml

### Pod CrashLoopBackOff

**Symptom**: Pod restarts repeatedly

**Diagnosis**:
```bash
# Check previous pod logs
kubectl logs -n pattern-agentic pattern-tts-<pod-id> --previous

# Check events
kubectl get events -n pattern-agentic --sort-by='.lastTimestamp' | grep pattern-tts
```

**Common fixes**:
```bash
# Increase readiness probe delay (race condition fix)
kubectl patch deployment pattern-tts -n pattern-agentic -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"tts-service","readinessProbe":{"initialDelaySeconds":30}}]}}}}'
```

### Slow Performance

**Diagnosis**:
```bash
# Check CPU throttling
kubectl top pods -n pattern-agentic | grep pattern-tts

# Check concurrent requests in logs
kubectl logs -n pattern-agentic -l app=pattern-tts-service | grep "INFO:.*POST /v1/audio/speech"
```

**Solutions**:
1. Increase CPU limits
2. Scale to more replicas
3. Enable GPU (future enhancement)

### Voice File Not Found

**Error**: `FileNotFoundError: /models/af_sky.pt`

**Check PVC**:
```bash
kubectl exec -n pattern-agentic pvc-uploader -- ls -lh /models/*.pt
```

**Fix**: Upload missing voice files (see PVC Management above)

---

## 📦 Code Structure

```
pattern-tts-service/
├── src/pattern_tts/
│   ├── api/
│   │   ├── main.py                    # FastAPI app
│   │   └── routers/
│   │       └── openai_compatible.py   # OpenAI endpoints
│   ├── services/
│   │   ├── model_manager.py           # Kokoro TTS wrapper
│   │   └── voice_manager.py           # Voice metadata
│   └── core/
│       └── config.py                  # Settings
├── helm/pattern-tts/
│   ├── Chart.yaml                     # Helm metadata
│   ├── values.yaml                    # Default values
│   ├── values-dev.yaml                # Dev overrides
│   ├── values-prod.yaml               # Prod overrides
│   └── templates/
│       ├── deployment.yaml            # K8s Deployment
│       ├── service.yaml               # K8s Service
│       ├── hpa.yaml                   # Autoscaler
│       └── pvc.yaml                   # Persistent volume
├── docker/
│   └── Dockerfile                     # Multi-stage build
├── tests/
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── e2e/                           # End-to-end tests
├── .mr_ai/agents/work_orders/         # Implementation docs
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
└── README.md                          # User documentation
```

---

## 🛠️ Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/add-new-voice

# Make changes
vim src/pattern_tts/services/voice_manager.py

# Run tests
pytest tests/unit/test_voice_manager.py -v

# Run linting
ruff check src/
black src/

# Commit
git add .
git commit -m "feat: Add new voice support"

# Push
git push origin feature/add-new-voice
```

### 2. Testing Changes

```bash
# Local testing
uvicorn src.pattern_tts.api.main:app --reload

# Build Docker image
docker build -t pattern-tts-service:test -f docker/Dockerfile .

# Test in Docker
docker run -p 8205:8205 pattern-tts-service:test

# Deploy to dev K8s
helm upgrade pattern-tts helm/pattern-tts \
  -f helm/pattern-tts/values-dev.yaml \
  --set tts.image.tag=test \
  -n pattern-agentic
```

### 3. Production Deployment

```bash
# Tag release
git tag -a v1.0.4 -m "Release v1.0.4: Add new voices"

# Build production image
docker build -t pattern-tts-service:v1.0.4 -f docker/Dockerfile .

# Push to ECR
aws ecr get-login-password --region us-west-2 --profile pattern-dev | \
  docker login --username AWS --password-stdin \
  085016484061.dkr.ecr.us-west-2.amazonaws.com

docker tag pattern-tts-service:v1.0.4 \
  085016484061.dkr.ecr.us-west-2.amazonaws.com/pattern-tts-service:v1.0.4

docker push 085016484061.dkr.ecr.us-west-2.amazonaws.com/pattern-tts-service:v1.0.4

# Deploy to prod
helm upgrade pattern-tts helm/pattern-tts \
  -f helm/pattern-tts/values-prod.yaml \
  --set tts.image.tag=v1.0.4 \
  -n pattern-agentic
```

---

## 📊 Performance Profiling

### CPU Profiling

```python
# Add to main.py for profiling
import cProfile
import pstats

def profile_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

### Memory Profiling

```bash
# Install memory-profiler
pip install memory-profiler

# Decorate function
@profile
def generate_speech(...):
    ...

# Run with profiler
python -m memory_profiler src/pattern_tts/services/model_manager.py
```

### Load Testing

```bash
# Install hey (HTTP load generator)
go install github.com/rakyll/hey@latest

# Run load test (1000 requests, 10 concurrent)
hey -n 1000 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Load test","voice":"alloy"}' \
  http://localhost:8205/v1/audio/speech
```

---

## 📝 Code Style Guidelines

### Python Style

- **Line length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff
- **Type hints**: Required for public functions
- **Docstrings**: Google style

```python
# Example
async def generate_speech(
    text: str,
    voice: str = "af_sky",
    speed: float = 1.0
) -> bytes:
    """Generate speech audio from text.
    
    Args:
        text: Text to synthesize (max 4096 characters)
        voice: Voice ID from voice_manager.VOICES
        speed: Speech rate (0.25 to 4.0)
    
    Returns:
        MP3 audio bytes (24kHz, 64kbps, mono)
    
    Raises:
        ValueError: If voice not found or text too long
    """
    ...
```

### Commit Messages

Follow Conventional Commits:

```
feat: Add new voice support
fix: Resolve PVC mount race condition
docs: Update API examples in README
test: Add integration tests for voices endpoint
refactor: Extract voice mapping to separate module
```

---

## 🎯 Next Steps for Contributors

1. **Read**: [README.md](README.md) for API overview
2. **Setup**: Follow "Development Setup" section above
3. **Test**: Run local service and try examples
4. **Explore**: Check Swagger UI at http://localhost:8205/docs
5. **Contribute**: Pick issue from `.mr_ai/agents/work_orders/`

---

**Happy Coding!** 🚀

**Never Fade to Black** 🏴‍☠️
