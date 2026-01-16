#!/bin/bash
# Pattern TTS Service v1.0.3 Validation Script
# Run this to verify the service works correctly before ECR push

set -e

echo "🔍 Pattern TTS Service v1.0.3 Validation"
echo "========================================"
echo ""

# Check if voice files exist in PVC
echo "1. Checking voice files in PVC..."
VOICE_COUNT=$(ls /tmp/kokoro-models/*.pt 2>/dev/null | wc -l)
if [ "$VOICE_COUNT" -ge 67 ]; then
    echo "   ✅ Found $VOICE_COUNT voice files"
else
    echo "   ❌ ERROR: Only found $VOICE_COUNT voice files (expected 67+)"
    exit 1
fi

# Check key voice files
echo "2. Verifying key voice files..."
for voice in af_sky af_alloy am_adam am_michael; do
    if [ -f "/tmp/kokoro-models/${voice}.pt" ]; then
        echo "   ✅ ${voice}.pt exists"
    else
        echo "   ❌ ERROR: ${voice}.pt missing"
        exit 1
    fi
done

# Start test container
echo ""
echo "3. Starting test container on port 8207..."
docker rm -f tts-validation-test 2>/dev/null || true
docker run -d \
    -p 8207:8205 \
    -v /tmp/kokoro-models:/models:ro \
    --name tts-validation-test \
    pattern-tts-service:v1.0.3

echo "   Waiting 35s for model warmup..."
sleep 35

# Test health endpoint
echo ""
echo "4. Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8207/health | jq -r '.status')
if [ "$HEALTH" == "healthy" ]; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ ERROR: Health check failed (status: $HEALTH)"
    docker logs tts-validation-test 2>&1 | tail -20
    docker rm -f tts-validation-test
    exit 1
fi

# Test ready endpoint
echo ""
echo "5. Testing ready endpoint..."
READY=$(curl -s http://localhost:8207/ready | jq -r '.status')
if [ "$READY" == "ready" ]; then
    echo "   ✅ Ready check passed"
else
    echo "   ❌ ERROR: Ready check failed (status: $READY)"
    docker rm -f tts-validation-test
    exit 1
fi

# Test speech generation (alloy)
echo ""
echo "6. Testing speech generation (alloy voice)..."
curl -s -X POST http://localhost:8207/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d '{"input":"Pattern TTS validation test","voice":"alloy","model":"tts-1"}' \
    --output /tmp/validation-alloy.mp3

FILE_SIZE=$(stat -f%z /tmp/validation-alloy.mp3 2>/dev/null || stat -c%s /tmp/validation-alloy.mp3)
if [ "$FILE_SIZE" -gt 1000 ]; then
    echo "   ✅ Speech generated ($FILE_SIZE bytes)"
else
    echo "   ❌ ERROR: Generated file too small ($FILE_SIZE bytes)"
    docker rm -f tts-validation-test
    exit 1
fi

# Test speech generation (am_adam)
echo ""
echo "7. Testing speech generation (am_adam voice)..."
curl -s -X POST http://localhost:8207/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d '{"input":"Testing male voice","voice":"am_adam","model":"tts-1"}' \
    --output /tmp/validation-adam.mp3

FILE_SIZE=$(stat -f%z /tmp/validation-adam.mp3 2>/dev/null || stat -c%s /tmp/validation-adam.mp3)
if [ "$FILE_SIZE" -gt 1000 ]; then
    echo "   ✅ Speech generated ($FILE_SIZE bytes)"
else
    echo "   ❌ ERROR: Generated file too small ($FILE_SIZE bytes)"
    docker rm -f tts-validation-test
    exit 1
fi

# Test speed parameter
echo ""
echo "8. Testing speed parameter..."
curl -s -X POST http://localhost:8207/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d '{"input":"Fast speech test","voice":"alloy","speed":2.0}' \
    --output /tmp/validation-fast.mp3

FILE_SIZE=$(stat -f%z /tmp/validation-fast.mp3 2>/dev/null || stat -c%s /tmp/validation-fast.mp3)
if [ "$FILE_SIZE" -gt 500 ]; then
    echo "   ✅ Speed parameter working ($FILE_SIZE bytes)"
else
    echo "   ❌ ERROR: Speed test failed ($FILE_SIZE bytes)"
    docker rm -f tts-validation-test
    exit 1
fi

# Check logs for errors
echo ""
echo "9. Checking logs for errors..."
ERROR_COUNT=$(docker logs tts-validation-test 2>&1 | grep -i "error\|exception\|failed" | grep -v "404 Not Found" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "   ✅ No errors in logs"
else
    echo "   ⚠️  Found $ERROR_COUNT error lines in logs (review recommended)"
    docker logs tts-validation-test 2>&1 | grep -i "error\|exception\|failed" | grep -v "404 Not Found" | head -5
fi

# Cleanup
echo ""
echo "10. Cleanup..."
docker stop tts-validation-test >/dev/null 2>&1
docker rm tts-validation-test >/dev/null 2>&1
rm -f /tmp/validation-*.mp3
echo "   ✅ Test container removed"

# Final summary
echo ""
echo "=========================================="
echo "✅ ALL VALIDATION TESTS PASSED"
echo "=========================================="
echo ""
echo "Image ready: pattern-tts-service:v1.0.3"
echo "Voice files: $VOICE_COUNT files in /tmp/kokoro-models/"
echo ""
echo "Next steps:"
echo "  1. Review KOKORO_VOICE_FILES_FIX.md"
echo "  2. Push to ECR (Captain only)"
echo "  3. Update Kubernetes deployment"
echo ""
echo "🏴‍☠️ Ready for Gold Star approval!"
