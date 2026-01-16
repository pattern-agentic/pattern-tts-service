"""Model management for Kokoro TTS inference"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from kokoro import KModel, KPipeline
from loguru import logger

from ..core.config import settings
from ..services.voice_manager import VoiceManager


class ModelManager:
    """Singleton manager for Kokoro TTS model

    Handles model loading, initialization, and audio generation
    with proper device management (CPU/CUDA/MPS).
    """

    # Singleton instance
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, model_path: str = "/models"):
        """Initialize model manager

        Args:
            model_path: Path to directory containing model files
        """
        self.model_path = Path(model_path)
        self.model: Optional[KModel] = None
        self.pipeline: Optional[KPipeline] = None
        self.device: str = settings.get_device()
        self._initialized = False

        logger.debug(f"ModelManager created with device: {self.device}")

    @classmethod
    async def get_instance(cls, model_path: str = "/models") -> "ModelManager":
        """Get singleton instance (thread-safe)

        Args:
            model_path: Path to model directory

        Returns:
            ModelManager singleton instance
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_path)
        return cls._instance

    async def initialize(self) -> None:
        """Load model asynchronously on startup

        Raises:
            RuntimeError: If model loading fails
        """
        if self._initialized:
            logger.debug("Model already initialized")
            return

        try:
            # Determine model file paths
            model_file = self.model_path / "kokoro-v1_0.pth"
            config_file = self.model_path / "config.json"

            # Verify files exist
            if not model_file.exists():
                raise FileNotFoundError(
                    f"Model file not found: {model_file}\n"
                    f"Expected location: {self.model_path}"
                )

            if not config_file.exists():
                raise FileNotFoundError(
                    f"Config file not found: {config_file}\n"
                    f"Expected location: {self.model_path}"
                )

            logger.info(f"Loading Kokoro model from {model_file}")
            logger.info(f"Using config: {config_file}")
            logger.info(f"Target device: {self.device}")

            # Load model with config
            self.model = KModel(
                config=str(config_file),
                model=str(model_file)
            ).eval()

            # Move to appropriate device
            if self.device == "cuda":
                self.model = self.model.cuda()
                logger.info("Model loaded on CUDA")
            elif self.device == "mps":
                self.model = self.model.to(torch.device("mps"))
                logger.info("Model loaded on MPS (Apple Silicon)")
            else:
                self.model = self.model.cpu()
                logger.info("Model loaded on CPU")

            # Create pipeline with default language
            self.pipeline = KPipeline(
                lang_code="a",  # American English
                model=self.model,
                device=self.device
            )

            self._initialized = True
            logger.info("Kokoro model initialized successfully")

        except FileNotFoundError as e:
            logger.error(f"Model files not found: {e}")
            raise RuntimeError(f"Failed to initialize model: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise RuntimeError(f"Model initialization failed: {e}")

    async def initialize_with_warmup(
        self, voice_manager: VoiceManager
    ) -> tuple[str, str, int]:
        """Initialize model and perform warmup inference

        Args:
            voice_manager: VoiceManager instance for getting voice count

        Returns:
            Tuple of (device, model_name, voice_count)

        Raises:
            RuntimeError: If initialization or warmup fails
        """
        import time

        start = time.perf_counter()

        try:
            # Initialize model
            await self.initialize()

            # Perform warmup generation
            warmup_text = "Pattern TTS service initialized successfully."
            voice = voice_manager.get_default_voice()

            logger.info(f"Warming up model with voice '{voice}'")

            # Generate warmup audio (discard output)
            _ = await self.generate_speech(warmup_text, voice=voice, speed=1.0)

            # Calculate warmup time
            warmup_ms = int((time.perf_counter() - start) * 1000)
            logger.info(f"Model warmup completed in {warmup_ms}ms")

            # Get voice count
            voice_count = len(voice_manager.get_voice_ids())

            return self.device, "kokoro-v1.0", voice_count

        except Exception as e:
            logger.error(f"Model warmup failed: {e}")
            raise RuntimeError(f"Failed to warm up model: {e}")

    def is_ready(self) -> bool:
        """Check if model is loaded and ready

        Returns:
            True if model is initialized and ready for inference
        """
        return self._initialized and self.model is not None and self.pipeline is not None

    async def generate_speech(
        self,
        text: str,
        voice: str = "af_sky",
        speed: float = 1.0
    ) -> bytes:
        """Generate audio from text

        Args:
            text: Text to synthesize
            voice: Voice ID (af_sky, af, am, etc.)
            speed: Speech rate multiplier (0.5 - 2.0)

        Returns:
            Audio data as MP3 bytes

        Raises:
            RuntimeError: If model not ready or generation fails
        """
        if not self.is_ready():
            raise RuntimeError("Model not initialized. Call initialize() first.")

        try:
            # Load voice tensor from PVC
            voice_path = f"/models/{voice}.pt"

            if not os.path.exists(voice_path):
                raise FileNotFoundError(
                    f"Voice file not found: {voice_path}\n"
                    f"Available voices should be in /models/"
                )

            # Load voice tensor
            voice_tensor = torch.load(voice_path, map_location=self.device)

            # Generate audio using pipeline
            # The pipeline handles text-to-phoneme and synthesis
            # It returns a generator of Result objects with .audio attribute
            audio_generator = self.pipeline(
                text,
                voice=voice_tensor,
                speed=speed,
                split_pattern=r'\n'  # Split on newlines for better quality
            )

            # Collect all audio chunks from the generator
            audio_chunks = []
            for result in audio_generator:
                # KPipeline.Result has an .audio attribute containing numpy array
                if hasattr(result, 'audio'):
                    audio_data = result.audio
                    if isinstance(audio_data, torch.Tensor):
                        audio_data = audio_data.cpu().numpy()
                    if isinstance(audio_data, np.ndarray) and audio_data.size > 0:
                        audio_chunks.append(audio_data)

            # Concatenate all chunks
            if not audio_chunks:
                raise RuntimeError(f"No audio generated from text: '{text[:50]}...'")

            audio_array = np.concatenate(audio_chunks)

            # Convert to int16 format for audio export
            audio_int16 = (audio_array * 32767).astype(np.int16)

            # Convert to MP3 using pydub
            from io import BytesIO
            from pydub import AudioSegment

            # Create AudioSegment from numpy array
            audio_segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=24000,
                sample_width=2,
                channels=1
            )

            # Export as MP3
            buffer = BytesIO()
            audio_segment.export(buffer, format="mp3", bitrate="24k")
            buffer.seek(0)

            return buffer.read()

        except FileNotFoundError as e:
            logger.error(f"Voice file not found: {e}")
            raise RuntimeError(f"Voice not available: {e}")
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise RuntimeError(f"Failed to generate speech: {e}")

    def get_supported_voices(self) -> list[str]:
        """Return list of available voices

        This is a convenience method that scans the /models directory
        for .pt voice files.

        Returns:
            List of voice IDs (without .pt extension)
        """
        try:
            voice_files = list(self.model_path.glob("*.pt"))
            voices = [f.stem for f in voice_files]
            logger.debug(f"Found {len(voices)} voice files in {self.model_path}")
            return sorted(voices)
        except Exception as e:
            logger.warning(f"Failed to scan for voices: {e}")
            return []

    def unload(self) -> None:
        """Unload model and free resources"""
        if self.model is not None:
            del self.model
            self.model = None

        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None

        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

        self._initialized = False
        logger.info("Model unloaded and resources freed")
