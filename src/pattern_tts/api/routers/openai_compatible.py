"""OpenAI-compatible TTS endpoint for Pattern TTS Service"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/v1",
    tags=["OpenAI Compatible"],
)


class SpeechRequest(BaseModel):
    """OpenAI-compatible TTS request schema

    Matches the OpenAI API specification for text-to-speech.
    """

    model: str = Field(
        default="tts-1",
        description="Model ID (tts-1 or tts-1-hd)"
    )
    input: str = Field(
        ...,
        max_length=4096,
        description="Text to synthesize (max 4096 characters)"
    )
    voice: str = Field(
        default="alloy",
        description="Voice ID (alloy, echo, fable, onyx, nova, shimmer)"
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Speech rate multiplier (0.25 - 4.0)"
    )
    response_format: str = Field(
        default="mp3",
        description="Audio format (mp3, opus, aac, flac)"
    )


# Voice mapping: OpenAI voice names → Kokoro voice IDs
VOICE_MAPPING = {
    "alloy": "af_sky",      # Female, clear
    "echo": "am",           # Male
    "fable": "af",          # Female
    "onyx": "am_adam",      # Male, deep
    "nova": "af_bella",     # Female, warm
    "shimmer": "af_sarah"   # Female, bright
}

# Supported models (both map to same Kokoro model)
SUPPORTED_MODELS = {"tts-1", "tts-1-hd", "kokoro"}


@router.post("/audio/speech")
async def create_speech(request: SpeechRequest, fastapi_request: Request):
    """OpenAI-compatible endpoint for text-to-speech

    Accepts OpenAI-style TTS requests and returns MP3 audio.

    Args:
        request: SpeechRequest with text, voice, and parameters
        fastapi_request: FastAPI request object for app state access

    Returns:
        Response with audio/mpeg content

    Raises:
        HTTPException: For validation errors or generation failures
    """
    # Validate model
    if request.model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_model",
                "message": f"Unsupported model: {request.model}. Supported: {', '.join(SUPPORTED_MODELS)}",
                "type": "invalid_request_error"
            }
        )

    # Validate input length
    if len(request.input) > 4096:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "message": f"Input text too long: {len(request.input)} chars (max 4096)",
                "type": "invalid_request_error"
            }
        )

    # Validate input not empty
    if not request.input.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": "Input text cannot be empty",
                "type": "invalid_request_error"
            }
        )

    try:
        # Get managers from app state
        model_manager = fastapi_request.app.state.model_manager
        voice_manager = fastapi_request.app.state.voice_manager

        # Check model is ready
        if not model_manager.is_ready():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "service_unavailable",
                    "message": "TTS model not ready",
                    "type": "server_error"
                }
            )

        # Map OpenAI voice to Kokoro voice
        kokoro_voice = VOICE_MAPPING.get(request.voice, request.voice)

        # Validate voice exists
        if not voice_manager.validate_voice(kokoro_voice):
            available_openai = list(VOICE_MAPPING.keys())
            available_kokoro = voice_manager.get_voice_ids()
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_voice",
                    "message": f"Voice '{request.voice}' not found. "
                               f"OpenAI voices: {', '.join(available_openai)}. "
                               f"Kokoro voices: {', '.join(available_kokoro)}",
                    "type": "invalid_request_error"
                }
            )

        logger.info(
            f"Generating speech: voice={request.voice}→{kokoro_voice}, "
            f"speed={request.speed}, length={len(request.input)} chars"
        )

        # Generate audio
        audio_bytes = await model_manager.generate_speech(
            text=request.input,
            voice=kokoro_voice,
            speed=request.speed
        )

        # Return audio response
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech.{request.response_format}",
                "Cache-Control": "no-cache"
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except FileNotFoundError as e:
        logger.error(f"Voice file not found: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "voice_unavailable",
                "message": f"Voice '{kokoro_voice}' files not available",
                "type": "server_error"
            }
        )
    except RuntimeError as e:
        logger.error(f"Speech generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "generation_failed",
                "message": str(e),
                "type": "server_error"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in speech generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "type": "server_error"
            }
        )


@router.get("/models")
async def list_models():
    """List available TTS models

    Returns OpenAI-compatible model list.

    Returns:
        Dict with model list
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "tts-1",
                "object": "model",
                "created": 1699046400,
                "owned_by": "pattern-tts"
            },
            {
                "id": "tts-1-hd",
                "object": "model",
                "created": 1699046400,
                "owned_by": "pattern-tts"
            },
            {
                "id": "kokoro",
                "object": "model",
                "created": 1699046400,
                "owned_by": "pattern-tts"
            }
        ]
    }


@router.get("/audio/voices")
async def list_voices(request: Request):
    """List available voices with metadata

    Returns both OpenAI-compatible and native Kokoro voices.

    Args:
        request: FastAPI request for app state access

    Returns:
        Dict with voice list
    """
    try:
        voice_manager = request.app.state.voice_manager

        # Get all voices with metadata
        all_voices = voice_manager.list_voices()

        # Add OpenAI voice mappings
        openai_voices = [
            {
                "id": openai_id,
                "name": f"{openai_id.capitalize()} (OpenAI)",
                "kokoro_voice": kokoro_id,
                "metadata": voice_manager.get_voice_info(kokoro_id)
            }
            for openai_id, kokoro_id in VOICE_MAPPING.items()
        ]

        return {
            "openai_compatible": openai_voices,
            "kokoro_native": all_voices
        }

    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to retrieve voice list",
                "type": "server_error"
            }
        )
