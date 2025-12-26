"""Base exporter class for all export formats."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from youtube_to_article.models.schemas import FinalOutput


class BaseExporter(ABC):
    """Abstract base class for export formats."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize exporter.

        Args:
            output_dir: Directory to save exported files. If None, uses current directory.
        """
        self.output_dir = output_dir or Path(".")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export(self, final_output: FinalOutput, filename: Optional[str] = None) -> Path:
        """Export final output to specified format.

        Args:
            final_output: Complete pipeline output to export.
            filename: Optional custom filename (without extension).

        Returns:
            Path to the exported file.
        """
        pass

    def get_default_filename(self, final_output: FinalOutput) -> str:
        """Generate default filename from article slug or video ID.

        Args:
            final_output: Pipeline output.

        Returns:
            Filename without extension.
        """
        if final_output.seo and final_output.seo.slug:
            return final_output.seo.slug
        return final_output.source_video.video_id

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this format (without dot)."""
        pass

    def get_output_path(self, filename: str) -> Path:
        """Get full output path with extension.

        Args:
            filename: Filename without extension.

        Returns:
            Full path with extension.
        """
        return self.output_dir / f"{filename}.{self.file_extension}"
