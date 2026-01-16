"""Voice metadata management and validation for Pattern TTS Service"""

from typing import Dict, List, Optional

from loguru import logger


class VoiceManager:
    """Manager for TTS voice metadata and validation

    Provides voice registry, validation, and metadata management
    for Kokoro TTS voices with OpenAI compatibility.
    """

    # Voice registry with metadata (expandable)
    # Format: voice_id -> metadata dict
    VOICES: Dict[str, Dict[str, any]] = {
        # Female voices
        "af_sky": {
            "name": "Sky (Female)",
            "lang": "en-us",
            "gender": "female",
            "style": "clear",
            "sample_rate": 24000,
            "description": "Clear, professional female voice"
        },
        "af": {
            "name": "Female Voice",
            "lang": "en-us",
            "gender": "female",
            "sample_rate": 24000,
            "description": "Standard female voice"
        },
        "af_bella": {
            "name": "Bella (Female)",
            "lang": "en-us",
            "gender": "female",
            "style": "warm",
            "sample_rate": 24000,
            "description": "Warm, friendly female voice"
        },
        "af_sarah": {
            "name": "Sarah (Female)",
            "lang": "en-us",
            "gender": "female",
            "style": "bright",
            "sample_rate": 24000,
            "description": "Bright, energetic female voice"
        },
        "af_heart": {
            "name": "Heart (Female)",
            "lang": "en-us",
            "gender": "female",
            "style": "expressive",
            "sample_rate": 24000,
            "description": "Expressive female voice"
        },
        "bf_emma": {
            "name": "Emma (British Female)",
            "lang": "en-gb",
            "gender": "female",
            "style": "clear",
            "sample_rate": 24000,
            "description": "British female voice"
        },
        "bf_isabella": {
            "name": "Isabella (British Female)",
            "lang": "en-gb",
            "gender": "female",
            "style": "elegant",
            "sample_rate": 24000,
            "description": "Elegant British female voice"
        },

        # Male voices
        "am": {
            "name": "Male Voice",
            "lang": "en-us",
            "gender": "male",
            "sample_rate": 24000,
            "description": "Standard male voice"
        },
        "am_adam": {
            "name": "Adam (Male)",
            "lang": "en-us",
            "gender": "male",
            "style": "deep",
            "sample_rate": 24000,
            "description": "Deep, authoritative male voice"
        },
        "am_michael": {
            "name": "Michael (Male)",
            "lang": "en-us",
            "gender": "male",
            "style": "smooth",
            "sample_rate": 24000,
            "description": "Smooth male voice"
        },
        "bm_george": {
            "name": "George (British Male)",
            "lang": "en-gb",
            "gender": "male",
            "style": "formal",
            "sample_rate": 24000,
            "description": "Formal British male voice"
        },
        "bm_lewis": {
            "name": "Lewis (British Male)",
            "lang": "en-gb",
            "gender": "male",
            "style": "casual",
            "sample_rate": 24000,
            "description": "Casual British male voice"
        },
    }

    # Default voice for the system
    DEFAULT_VOICE: str = "af_sky"

    def __init__(self):
        """Initialize voice manager"""
        logger.debug(f"VoiceManager initialized with {len(self.VOICES)} voices")

    def validate_voice(self, voice: str) -> bool:
        """Check if voice ID is valid

        Args:
            voice: Voice ID to validate

        Returns:
            True if voice exists in registry, False otherwise
        """
        return voice in self.VOICES

    def get_voice_info(self, voice: str) -> Optional[Dict[str, any]]:
        """Get metadata for specific voice

        Args:
            voice: Voice ID to retrieve info for

        Returns:
            Dictionary with voice metadata, or None if voice not found
        """
        return self.VOICES.get(voice)

    def list_voices(self) -> List[Dict[str, any]]:
        """Return all available voices with metadata

        Returns:
            List of dictionaries containing voice ID and metadata
        """
        return [
            {"id": voice_id, **metadata}
            for voice_id, metadata in self.VOICES.items()
        ]

    def get_default_voice(self) -> str:
        """Return default voice ID

        Returns:
            Default voice ID (af_sky)
        """
        return self.DEFAULT_VOICE

    def get_voice_ids(self) -> List[str]:
        """Get list of all available voice IDs

        Returns:
            List of voice ID strings
        """
        return list(self.VOICES.keys())

    def get_voices_by_gender(self, gender: str) -> List[str]:
        """Get voices filtered by gender

        Args:
            gender: Gender to filter by ('male' or 'female')

        Returns:
            List of voice IDs matching the gender
        """
        return [
            voice_id
            for voice_id, metadata in self.VOICES.items()
            if metadata.get("gender") == gender.lower()
        ]

    def get_voices_by_language(self, lang: str) -> List[str]:
        """Get voices filtered by language

        Args:
            lang: Language code to filter by (e.g., 'en-us', 'en-gb')

        Returns:
            List of voice IDs matching the language
        """
        return [
            voice_id
            for voice_id, metadata in self.VOICES.items()
            if metadata.get("lang") == lang.lower()
        ]

    def get_sample_rate(self, voice: str) -> int:
        """Get sample rate for a specific voice

        Args:
            voice: Voice ID

        Returns:
            Sample rate in Hz, or 24000 as default
        """
        voice_info = self.get_voice_info(voice)
        return voice_info.get("sample_rate", 24000) if voice_info else 24000
