"""Agent 1: Transcriber - Extracts and transcribes YouTube videos."""
import os
import json
import logging
from pathlib import Path
from typing import Optional

from tools.youtube_tools import (
    extract_video_id,
    get_video_metadata,
    extract_captions,
    download_audio,
    cleanup_audio_file,
)
from tools.whisper_tools import WhisperTranscriber
from models.schemas import TranscriptResult, TranscriptSegment, VideoMetadata
from config.settings import PipelineConfig

logger = logging.getLogger(__name__)


class TranscriberAgent:
    """
    Agent 1: Transcriber

    Extracts transcripts from YouTube videos using a two-tier approach:
    1. Try existing captions (fast, free)
    2. Fallback to Whisper transcription (slower, but works when captions unavailable)

    Includes caching to avoid re-transcribing the same video.
    """

    def __init__(self, config: PipelineConfig, cache_dir: str = "./cache"):
        """
        Initialize the Transcriber agent.

        Args:
            config: Pipeline configuration
            cache_dir: Directory for caching transcripts
        """
        self.config = config
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Lazy-load Whisper model (only if needed)
        self._whisper = None

        logger.info("Transcriber agent initialized")

    def _get_whisper(self) -> WhisperTranscriber:
        """Lazy-load Whisper model."""
        if self._whisper is None:
            logger.info("Loading Whisper model...")
            self._whisper = WhisperTranscriber(
                model_size=self.config.whisper_model,
                device=self.config.whisper_device,
                compute_type=self.config.whisper_compute_type
            )
        return self._whisper

    def _get_cache_path(self, video_id: str) -> Path:
        """Get cache file path for a video."""
        return self.cache_dir / f"{video_id}_transcript.json"

    def _load_from_cache(self, video_id: str) -> Optional[TranscriptResult]:
        """Load cached transcript if available."""
        cache_path = self._get_cache_path(video_id)

        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded transcript from cache: {video_id}")
                    return TranscriptResult(**data)
            except Exception as e:
                logger.warning(f"Failed to load cache for {video_id}: {e}")

        return None

    def _save_to_cache(self, video_id: str, transcript: TranscriptResult):
        """Save transcript to cache."""
        cache_path = self._get_cache_path(video_id)

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(transcript.model_dump(), f, indent=2, default=str)
            logger.info(f"Saved transcript to cache: {video_id}")
        except Exception as e:
            logger.warning(f"Failed to save cache for {video_id}: {e}")

    def run(self, youtube_url: str, force_whisper: bool = False) -> TranscriptResult:
        """
        Extract transcript from YouTube video.

        Args:
            youtube_url: YouTube video URL or ID
            force_whisper: If True, skip captions and use Whisper directly

        Returns:
            TranscriptResult with transcript data

        Raises:
            Exception: If transcription fails
        """
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        logger.info(f"Processing video: {video_id}")

        # Check cache first
        cached = self._load_from_cache(video_id)
        if cached is not None:
            return cached

        # Get video metadata
        logger.info("Fetching video metadata...")
        metadata = get_video_metadata(youtube_url)

        # Strategy 1: Try captions first (unless forced to use Whisper)
        transcript_data = None

        if not force_whisper:
            logger.info("Attempting to extract existing captions...")
            transcript_data = extract_captions(video_id)

        # Strategy 2: Fallback to Whisper if captions unavailable
        if transcript_data is None:
            logger.info("Captions unavailable, using Whisper transcription...")

            # Download audio
            audio_path = None
            try:
                audio_path = download_audio(youtube_url, output_dir="./temp")

                # Transcribe with Whisper
                whisper = self._get_whisper()
                transcript_data = whisper.transcribe_audio(audio_path)

            finally:
                # Always cleanup audio file
                if audio_path:
                    cleanup_audio_file(audio_path)

        # Build TranscriptResult
        result = TranscriptResult(
            video_id=video_id,
            title=metadata['title'],
            channel=metadata['channel'],
            duration_seconds=metadata['duration_seconds'],
            transcript=transcript_data['full_text'],
            segments=transcript_data['segments'],
            source=transcript_data['source'],
            language=transcript_data['language'],
            thumbnail_url=metadata.get('thumbnail_url'),
            upload_date=metadata.get('upload_date'),
        )

        # Cache the result
        self._save_to_cache(video_id, result)

        logger.info(
            f"Transcription complete: {len(result.segments)} segments, "
            f"source: {result.source}, language: {result.language}"
        )

        return result

    def clear_cache(self, video_id: Optional[str] = None):
        """
        Clear transcript cache.

        Args:
            video_id: Specific video ID to clear, or None to clear all
        """
        if video_id:
            cache_path = self._get_cache_path(video_id)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Cleared cache for {video_id}")
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*_transcript.json"):
                cache_file.unlink()
            logger.info("Cleared all transcript cache")


def create_transcriber_agent(config: Optional[PipelineConfig] = None) -> TranscriberAgent:
    """
    Factory function to create a Transcriber agent.

    Args:
        config: Pipeline configuration (loads from env if not provided)

    Returns:
        Configured TranscriberAgent instance
    """
    if config is None:
        from config.settings import get_config
        config = get_config()

    return TranscriberAgent(config)
