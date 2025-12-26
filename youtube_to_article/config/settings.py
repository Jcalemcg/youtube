"""Configuration management using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Literal


class PipelineConfig(BaseSettings):
    """Pipeline configuration loaded from environment variables."""

    # Hugging Face
    hf_token: str

    # Whisper configuration
    whisper_model: str = "base"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"

    # Model selection
    analyzer_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    writer_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    seo_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    # Output configuration
    output_dir: str = "./output"
    log_level: str = "INFO"

    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5

    # Rate limiting for HF API
    requests_per_minute: int = 30

    # FFmpeg configuration (optional, auto-detect if not set)
    ffmpeg_path: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_config() -> PipelineConfig:
    """Load and return pipeline configuration."""
    return PipelineConfig()
