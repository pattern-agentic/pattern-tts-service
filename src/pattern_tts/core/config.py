from pathlib import Path
from typing import List, Optional

import torch
from pydantic_settings import SettingsConfigDict
from pattern_agentic_settings import PABaseSettings


class Settings(PABaseSettings):
    model_config = SettingsConfigDict(env_prefix="PA_TTS_")

    api_title: str
    api_description: str

    log_level: str

    use_gpu: bool
    device_type: Optional[str] = None

    model_dir: str
    voices_dir: str
    default_voice: str
    sample_rate: int

    target_min_tokens: int
    target_max_tokens: int
    absolute_max_tokens: int
    advanced_text_normalization: bool
    voice_weight_normalization: bool

    gap_trim_ms: int
    dynamic_gap_trim_padding_ms: int
    dynamic_gap_trim_padding_char_multiplier: dict

    cors_origins: List[str]
    cors_enabled: bool

    download_model: bool

    def get_device(self) -> str:
        if not self.use_gpu:
            return "cpu"

        if self.device_type:
            return self.device_type

        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @property
    def model_path(self) -> Path:
        return Path(self.model_dir)

    @property
    def voices_path(self) -> Path:
        return Path(self.voices_dir)


settings = Settings.load('pattern_tts_service')
