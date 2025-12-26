"""Markdown format exporter."""
from pathlib import Path
from typing import Optional
from youtube_to_article.models.schemas import FinalOutput
from .base import BaseExporter


class MarkdownExporter(BaseExporter):
    """Export articles in Markdown format."""

    @property
    def file_extension(self) -> str:
        """Return file extension."""
        return "md"

    def export(self, final_output: FinalOutput, filename: Optional[str] = None) -> Path:
        """Export to Markdown format.

        Args:
            final_output: Pipeline output.
            filename: Optional custom filename.

        Returns:
            Path to exported file.
        """
        filename = filename or self.get_default_filename(final_output)
        output_path = self.get_output_path(filename)

        # Build markdown content
        content = self._build_markdown(final_output)

        # Write to file
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _build_markdown(self, final_output: FinalOutput) -> str:
        """Build markdown content from pipeline output.

        Args:
            final_output: Pipeline output.

        Returns:
            Formatted markdown string.
        """
        lines = []

        # Title
        lines.append(f"# {final_output.article.headline}\n")

        # Meta information
        lines.append("---")
        lines.append(f"Source: {final_output.source_video.title}")
        lines.append(f"Channel: {final_output.source_video.channel}")
        lines.append(f"Video ID: {final_output.source_video.video_id}")
        if final_output.seo:
            lines.append(f"Slug: {final_output.seo.slug}")
            lines.append(f"Keywords: {', '.join([final_output.seo.primary_keyword] + final_output.seo.secondary_keywords)}")
        lines.append(f"Generated: {final_output.generated_at.isoformat()}")
        lines.append("---\n")

        # Introduction
        lines.append(final_output.article.introduction)
        lines.append("")

        # Body sections
        for section in final_output.article.sections:
            lines.append(f"## {section.heading}\n")
            lines.append(section.content)
            lines.append("")

        # Conclusion
        lines.append("## Conclusion\n")
        lines.append(final_output.article.conclusion)
        lines.append("")

        # Footer with SEO info if available
        if final_output.seo:
            lines.append("---")
            lines.append("### SEO Metadata")
            lines.append(f"**Meta Title:** {final_output.seo.meta_title}")
            lines.append(f"**Meta Description:** {final_output.seo.meta_description}")

        return "\n".join(lines)
