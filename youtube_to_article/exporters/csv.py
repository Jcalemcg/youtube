"""CSV format exporter."""
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any
from youtube_to_article.models.schemas import FinalOutput
from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Export articles in CSV format for spreadsheet applications."""

    @property
    def file_extension(self) -> str:
        """Return file extension."""
        return "csv"

    def export(self, final_output: FinalOutput, filename: Optional[str] = None) -> Path:
        """Export to CSV format.

        Args:
            final_output: Pipeline output.
            filename: Optional custom filename.

        Returns:
            Path to exported file.
        """
        filename = filename or self.get_default_filename(final_output)
        output_path = self.get_output_path(filename)

        # Prepare data rows
        rows = self._prepare_data(final_output)

        # Write to CSV file
        if rows:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return output_path

    def _prepare_data(self, final_output: FinalOutput) -> List[Dict[str, Any]]:
        """Prepare data for CSV export.

        Args:
            final_output: Pipeline output.

        Returns:
            List of dictionaries for CSV rows.
        """
        rows = []

        # Add headline
        rows.append({
            "Type": "Headline",
            "Content": final_output.article.headline,
            "Additional": ""
        })

        # Add introduction
        rows.append({
            "Type": "Introduction",
            "Content": final_output.article.introduction,
            "Additional": ""
        })

        # Add sections
        for section in final_output.article.sections:
            rows.append({
                "Type": "Section Heading",
                "Content": section.heading,
                "Additional": f"Word Count: {section.word_count}"
            })
            rows.append({
                "Type": "Section Content",
                "Content": section.content,
                "Additional": ""
            })

        # Add conclusion
        rows.append({
            "Type": "Conclusion",
            "Content": final_output.article.conclusion,
            "Additional": ""
        })

        # Add metadata
        rows.append({
            "Type": "Metadata",
            "Content": "Source Video",
            "Additional": final_output.source_video.title
        })
        rows.append({
            "Type": "Metadata",
            "Content": "Channel",
            "Additional": final_output.source_video.channel
        })
        rows.append({
            "Type": "Metadata",
            "Content": "Video ID",
            "Additional": final_output.source_video.video_id
        })
        rows.append({
            "Type": "Metadata",
            "Content": "Video Duration",
            "Additional": f"{final_output.source_video.duration_seconds} seconds"
        })

        # Add SEO information if available
        if final_output.seo:
            rows.append({
                "Type": "SEO",
                "Content": "Meta Title",
                "Additional": final_output.seo.meta_title
            })
            rows.append({
                "Type": "SEO",
                "Content": "Meta Description",
                "Additional": final_output.seo.meta_description
            })
            rows.append({
                "Type": "SEO",
                "Content": "Slug",
                "Additional": final_output.seo.slug
            })
            rows.append({
                "Type": "SEO",
                "Content": "Primary Keyword",
                "Additional": final_output.seo.primary_keyword
            })
            rows.append({
                "Type": "SEO",
                "Content": "Secondary Keywords",
                "Additional": ", ".join(final_output.seo.secondary_keywords)
            })

        return rows
