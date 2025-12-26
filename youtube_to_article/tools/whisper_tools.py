"""Whisper transcription tools using faster-whisper."""
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from faster_whisper import WhisperModel

from models.schemas import TranscriptSegment

logger = logging.getLogger(__name__)


class WhisperToolsError(Exception):
    """Base exception for Whisper tools."""
    pass


class WhisperTranscriber:
    """Wrapper for faster-whisper transcription."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cuda",
        compute_type: str = "float16"
    ):
        """
        Initialize Whisper model.

        Args:
            model_size: Model size (tiny, base, small, medium, large-v3)
            device: Device to use (cuda, cpu)
            compute_type: Computation type (float16, int8, float32)

        Available models:
        - tiny: Fastest, least accurate (~1GB VRAM)
        - base: Good balance (~1GB VRAM)
        - small: Better accuracy (~2GB VRAM)
        - medium: High accuracy (~5GB VRAM)
        - large-v3: Best accuracy (~10GB VRAM)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

        logger.info(f"Initializing Whisper model: {model_size} on {device} with {compute_type}")

    def _load_model(self):
        """Lazy load the Whisper model."""
        if self.model is None:
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                logger.info(f"Whisper model loaded successfully: {self.model_size}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                # Fallback to CPU if CUDA fails
                if self.device == "cuda":
                    logger.warning("Falling back to CPU")
                    self.device = "cpu"
                    self.compute_type = "int8"  # More efficient on CPU
                    self.model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type
                    )
                else:
                    raise WhisperToolsError(f"Failed to load Whisper model: {e}")

    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using faster-whisper.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es'). None for auto-detection.
            task: 'transcribe' or 'translate' (to English)

        Returns:
            Dictionary with:
            {
                'segments': List[TranscriptSegment],
                'full_text': str,
                'language': str,
                'source': 'whisper'
            }

        Raises:
            WhisperToolsError: If transcription fails
        """
        # Ensure model is loaded
        self._load_model()

        # Verify audio file exists
        if not Path(audio_path).exists():
            raise WhisperToolsError(f"Audio file not found: {audio_path}")

        try:
            logger.info(f"Starting transcription of {audio_path}")

            # Transcribe with faster-whisper
            segments_generator, info = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                vad_filter=True,  # Voice activity detection to remove silence
                vad_parameters=dict(
                    min_silence_duration_ms=500
                )
            )

            # Process segments
            segments = []
            full_text_parts = []

            for segment in segments_generator:
                transcript_segment = TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                    confidence=segment.avg_logprob  # Use avg log probability as confidence
                )
                segments.append(transcript_segment)
                full_text_parts.append(segment.text.strip())

            # Detected language
            detected_language = info.language

            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"language: {detected_language}"
            )

            return {
                'segments': segments,
                'full_text': ' '.join(full_text_parts),
                'language': detected_language,
                'source': 'whisper'
            }

        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}")
            raise WhisperToolsError(f"Transcription failed: {e}")

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the loaded model."""
        return {
            'model_size': self.model_size,
            'device': self.device,
            'compute_type': self.compute_type,
            'loaded': self.model is not None
        }


# Convenience function for one-off transcriptions
def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    device: str = "cuda",
    compute_type: str = "float16",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe audio file using Whisper (convenience function).

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size
        device: Device to use (cuda/cpu)
        compute_type: Computation type
        language: Language code (None for auto-detection)

    Returns:
        Transcription result dictionary

    Raises:
        WhisperToolsError: If transcription fails
    """
    transcriber = WhisperTranscriber(
        model_size=model_size,
        device=device,
        compute_type=compute_type
    )

    return transcriber.transcribe_audio(audio_path, language=language)
