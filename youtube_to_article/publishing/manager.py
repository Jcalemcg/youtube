"""Publishing manager for coordinating exports and publishing."""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from youtube_to_article.models.schemas import FinalOutput
from youtube_to_article.exporters import (
    BaseExporter,
    MarkdownExporter,
    JSONExporter,
    HTMLExporter,
    CSVExporter,
)
from youtube_to_article.publishers.base import BasePublisher, PublishConfig, PublishingResult
from youtube_to_article.publishers.medium import MediumPublisher
from .history import PublishingHistory, PublishingHistoryManager


class PublishingManager:
    """Manage article exports and publishing to multiple platforms."""

    AVAILABLE_EXPORTERS = {
        "markdown": MarkdownExporter,
        "json": JSONExporter,
        "html": HTMLExporter,
        "csv": CSVExporter,
    }

    AVAILABLE_PUBLISHERS = {
        "medium": MediumPublisher,
    }

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        history_dir: Optional[Path] = None,
    ):
        """Initialize publishing manager.

        Args:
            output_dir: Directory for exported files.
            history_dir: Directory for publishing history.
        """
        self.output_dir = output_dir or Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.history_manager = PublishingHistoryManager(history_dir)
        self.publishers: Dict[str, BasePublisher] = {}

    def register_publisher(self, name: str, publisher: BasePublisher) -> None:
        """Register a publisher instance.

        Args:
            name: Publisher identifier (e.g., 'medium').
            publisher: Publisher instance.
        """
        self.publishers[name] = publisher

    def export(
        self,
        final_output: FinalOutput,
        formats: Optional[List[str]] = None,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """Export article in specified formats.

        Args:
            final_output: Complete pipeline output.
            formats: List of formats to export (defaults to all).
            output_dir: Override output directory.

        Returns:
            Dictionary mapping format names to export paths.
        """
        if formats is None:
            formats = list(self.AVAILABLE_EXPORTERS.keys())

        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        for fmt in formats:
            if fmt not in self.AVAILABLE_EXPORTERS:
                continue

            exporter_class = self.AVAILABLE_EXPORTERS[fmt]
            exporter = exporter_class(output_dir)

            try:
                path = exporter.export(final_output)
                results[fmt] = path
            except Exception as e:
                print(f"Error exporting to {fmt}: {e}")

        return results

    def export_single(
        self,
        final_output: FinalOutput,
        format: str,
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Export article in single format.

        Args:
            final_output: Complete pipeline output.
            format: Export format.
            output_dir: Override output directory.

        Returns:
            Path to exported file or None if failed.
        """
        result = self.export(final_output, formats=[format], output_dir=output_dir)
        return result.get(format)

    def publish(
        self,
        final_output: FinalOutput,
        platform: str,
        config: PublishConfig,
    ) -> PublishingResult:
        """Publish article to platform.

        Args:
            final_output: Complete pipeline output.
            platform: Platform name (e.g., 'medium').
            config: Publishing configuration.

        Returns:
            Publishing result.
        """
        if platform not in self.publishers:
            return self._create_error_result(
                platform, f"Publisher not registered: {platform}"
            )

        publisher = self.publishers[platform]

        try:
            result = publisher.publish(final_output, config)

            # Save to history
            article_slug = final_output.seo.slug if final_output.seo else final_output.source_video.video_id
            history = self.history_manager.get_or_create_history(
                final_output.source_video.video_id, article_slug
            )
            history.add_result(result)
            self.history_manager.save_history(history)

            return result

        except Exception as e:
            return self._create_error_result(platform, str(e))

    def publish_to_multiple(
        self,
        final_output: FinalOutput,
        platforms: List[str],
        config: Optional[PublishConfig] = None,
    ) -> Dict[str, PublishingResult]:
        """Publish article to multiple platforms.

        Args:
            final_output: Complete pipeline output.
            platforms: List of platform names.
            config: Publishing configuration (applied to all).

        Returns:
            Dictionary mapping platform names to results.
        """
        if config is None:
            from youtube_to_article.publishers.base import PublishingPlatform

            config = PublishConfig(platform=PublishingPlatform.MEDIUM)

        results = {}

        for platform in platforms:
            results[platform] = self.publish(final_output, platform, config)

        return results

    def export_and_publish(
        self,
        final_output: FinalOutput,
        export_formats: Optional[List[str]] = None,
        publish_to: Optional[List[Tuple[str, PublishConfig]]] = None,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, any]:
        """Export and publish article in one operation.

        Args:
            final_output: Complete pipeline output.
            export_formats: Formats to export.
            publish_to: List of (platform, config) tuples.
            output_dir: Output directory for exports.

        Returns:
            Dictionary with 'exports' and 'publishing' results.
        """
        exports = self.export(final_output, export_formats, output_dir)

        publishing_results = {}
        if publish_to:
            for platform, config in publish_to:
                publishing_results[platform] = self.publish(final_output, platform, config)

        return {
            "exports": exports,
            "publishing": publishing_results,
        }

    def get_publishing_history(self, video_id: str, article_slug: str) -> Optional[PublishingHistory]:
        """Get publishing history for article.

        Args:
            video_id: Video ID.
            article_slug: Article slug.

        Returns:
            Publishing history or None.
        """
        return self.history_manager.load_history(video_id, article_slug)

    def get_statistics(self) -> Dict[str, any]:
        """Get publishing statistics.

        Returns:
            Statistics dictionary.
        """
        return self.history_manager.get_statistics()

    def _create_error_result(self, platform: str, error: str) -> PublishingResult:
        """Create error result.

        Args:
            platform: Platform name.
            error: Error message.

        Returns:
            Publishing result with error.
        """
        from youtube_to_article.publishers.base import PublishingStatus, PublishingPlatform

        # Map platform string to enum
        try:
            platform_enum = PublishingPlatform[platform.upper()]
        except KeyError:
            platform_enum = PublishingPlatform.MEDIUM

        return PublishingResult(
            platform=platform_enum,
            status=PublishingStatus.FAILED,
            error=error,
        )
