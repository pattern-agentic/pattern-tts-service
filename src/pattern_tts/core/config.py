"""Configuration management for Pattern TTS Service"""

import os
from pathlib import Path
from typing import List

import torch
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration settings"""

    # API Settings
    api_title: str = "Pattern TTS Service"
    api_description: str = "OpenAI-compatible Text-to-Speech API using Kokoro TTS"
    api_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8205  # Audio services block (see PORT_RESERVATIONS.md)

    # Logging
    log_level: str = "INFO"  # DEBUG/INFO/WARNING/ERROR

    # GPU Settings
    use_gpu: bool = True
    device_type: str | None = None  # Auto-detected if None (cuda/cpu)

    # Model Settings
    model_dir: str = "/app/models/v1_0"
    voices_dir: str = "/app/voices/v1_0"
    default_voice: str = "af_heart"
    sample_rate: int = 24000

    # Text Processing
    target_min_tokens: int = 175
    target_max_tokens: int = 250
    absolute_max_tokens: int = 450
    advanced_text_normalization: bool = True
    voice_weight_normalization: bool = True

    # Audio Processing
    gap_trim_ms: int = 1
    dynamic_gap_trim_padding_ms: int = 410
    dynamic_gap_trim_padding_char_multiplier: dict = {
        ".": 1.0,
        "!": 0.9,
        "?": 1.0,
        ",": 0.8,
    }

    # CORS Settings
    cors_origins: List[str] = ["*"]
    cors_enabled: bool = True

    # Model Download
    download_model: bool = True  # Auto-download on startup if models missing

    class Config:
        env_file = ".env"
        env_prefix = "TTS_"  # Environment variables: TTS_PORT, TTS_LOG_LEVEL, etc.

    def get_device(self) -> str:
        """Get the appropriate device based on settings and availability"""
        if not self.use_gpu:
            return "cpu"

        if self.device_type:
            return self.device_type

        # Auto-detect device
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @property
    def model_path(self) -> Path:
        """Get path to model directory"""
        return Path(self.model_dir)

    @property
    def voices_path(self) -> Path:
        """Get path to voices directory"""
        return Path(self.voices_dir)


# Global settings instance
settings = Settings()
