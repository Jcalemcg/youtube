"""JSON format exporter."""
import json
from pathlib import Path
from typing import Optional
from youtube_to_article.models.schemas import FinalOutput
from .base import BaseExporter


class JSONExporter(BaseExporter):
    """Export articles in JSON format."""

    @property
    def file_extension(self) -> str:
        """Return file extension."""
        return "json"

    def export(self, final_output: FinalOutput, filename: Optional[str] = None) -> Path:
        """Export to JSON format.

        Args:
            final_output: Pipeline output.
            filename: Optional custom filename.

        Returns:
            Path to exported file.
        """
        filename = filename or self.get_default_filename(final_output)
        output_path = self.get_output_path(filename)

        # Convert to JSON-serializable dict
        data = final_output.model_dump(mode="json")

        # Write to file with pretty printing
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path
