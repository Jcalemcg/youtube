"""Test suite for publishing and export functionality."""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from youtube_to_article.models.schemas import (
    FinalOutput,
    VideoMetadata,
    TranscriptResult,
    TranscriptSegment,
    ContentAnalysis,
    Quote,
    SectionOutline,
    Article,
    ArticleSection,
    SEOPackage,
    SocialPosts,
)
from youtube_to_article.publishing.manager import PublishingManager
from youtube_to_article.publishers.base import PublishConfig, PublishingPlatform
from youtube_to_article.exporters import MarkdownExporter, JSONExporter, HTMLExporter, CSVExporter


@pytest.fixture
def sample_final_output():
    """Create sample FinalOutput for testing."""
    return FinalOutput(
        source_video=VideoMetadata(
            video_id="test123",
            url="https://youtube.com/watch?v=test123",
            title="Test Video Title",
            channel="Test Channel",
            duration_seconds=600,
            thumbnail_url="https://example.com/thumb.jpg",
            upload_date="2024-01-01",
        ),
        transcript=TranscriptResult(
            video_id="test123",
            title="Test Video Title",
            channel="Test Channel",
            duration_seconds=600,
            transcript="This is the full transcript of the test video...",
            segments=[
                TranscriptSegment(
                    start=0,
                    end=10,
                    text="First segment",
                )
            ],
            source="whisper",
            language="en",
        ),
        analysis=ContentAnalysis(
            main_topic="Testing article generation",
            subtopics=["Test", "Generation", "Publishing"],
            key_quotes=[
                Quote(text="Test quote", timestamp=5.0)
            ],
            data_points=["100% test coverage"],
            suggested_sections=[
                SectionOutline(title="Introduction", description="Intro section")
            ],
            target_audience="developers",
            tone="technical",
            estimated_reading_time=5,
        ),
        article=Article(
            headline="Test Article Title",
            introduction="This is a test article introduction.",
            sections=[
                ArticleSection(
                    heading="Test Section",
                    content="This is test content for the section.",
                    word_count=50,
                )
            ],
            conclusion="This is the test conclusion.",
            markdown="# Test Article\n\nContent here",
            word_count=200,
        ),
        seo=SEOPackage(
            meta_title="Test Article - Keywords",
            meta_description="Short description of test article",
            slug="test-article-title",
            primary_keyword="test",
            secondary_keywords=["article", "testing"],
            schema_markup={"@type": "Article"},
            open_graph={"title": "Test Article", "description": "Test description"},
            twitter_card={"title": "Test Article", "description": "Test description"},
            social_posts=SocialPosts(
                twitter="Check out this test article!",
                linkedin="Sharing a great test article",
                facebook="Read this test article",
            ),
            internal_link_suggestions=["related-article"],
        ),
    )


class TestExporters:
    """Test export functionality."""

    def test_markdown_exporter(self, sample_final_output, tmp_path):
        """Test Markdown export."""
        exporter = MarkdownExporter(output_dir=tmp_path)
        output_path = exporter.export(sample_final_output)

        assert output_path.exists()
        assert output_path.suffix == ".md"

        content = output_path.read_text()
        assert "Test Article Title" in content
        assert "Test Channel" in content
        assert "Test Section" in content

    def test_json_exporter(self, sample_final_output, tmp_path):
        """Test JSON export."""
        exporter = JSONExporter(output_dir=tmp_path)
        output_path = exporter.export(sample_final_output)

        assert output_path.exists()
        assert output_path.suffix == ".json"

        data = json.loads(output_path.read_text())
        assert data["source_video"]["video_id"] == "test123"
        assert data["article"]["headline"] == "Test Article Title"
        assert data["seo"]["slug"] == "test-article-title"

    def test_html_exporter(self, sample_final_output, tmp_path):
        """Test HTML export."""
        exporter = HTMLExporter(output_dir=tmp_path)
        output_path = exporter.export(sample_final_output)

        assert output_path.exists()
        assert output_path.suffix == ".html"

        content = output_path.read_text()
        assert "<html" in content
        assert "Test Article Title" in content
        assert "test-article-title" in content

    def test_csv_exporter(self, sample_final_output, tmp_path):
        """Test CSV export."""
        exporter = CSVExporter(output_dir=tmp_path)
        output_path = exporter.export(sample_final_output)

        assert output_path.exists()
        assert output_path.suffix == ".csv"

        content = output_path.read_text()
        assert "Headline" in content
        assert "Test Article Title" in content
        assert "Test Channel" in content

    def test_custom_filename(self, sample_final_output, tmp_path):
        """Test export with custom filename."""
        exporter = MarkdownExporter(output_dir=tmp_path)
        output_path = exporter.export(sample_final_output, filename="custom_name")

        assert output_path.name == "custom_name.md"

    def test_multiple_exports(self, sample_final_output, tmp_path):
        """Test exporting to multiple formats."""
        formats = ["markdown", "json", "html", "csv"]
        exporters = {
            "markdown": MarkdownExporter(output_dir=tmp_path),
            "json": JSONExporter(output_dir=tmp_path),
            "html": HTMLExporter(output_dir=tmp_path),
            "csv": CSVExporter(output_dir=tmp_path),
        }

        results = {}
        for fmt, exporter in exporters.items():
            results[fmt] = exporter.export(sample_final_output)

        # Verify all files exist
        assert len(results) == len(formats)
        for fmt, path in results.items():
            assert path.exists()


class TestPublishingManager:
    """Test publishing manager functionality."""

    def test_manager_export_single(self, sample_final_output, tmp_path):
        """Test single format export via manager."""
        manager = PublishingManager(output_dir=tmp_path)
        path = manager.export_single(sample_final_output, "markdown")

        assert path is not None
        assert path.exists()
        assert path.suffix == ".md"

    def test_manager_export_multiple(self, sample_final_output, tmp_path):
        """Test multiple format export via manager."""
        manager = PublishingManager(output_dir=tmp_path)
        exports = manager.export(
            sample_final_output,
            formats=["markdown", "json", "html"]
        )

        assert len(exports) == 3
        assert all(path.exists() for path in exports.values())

    def test_export_all_formats(self, sample_final_output, tmp_path):
        """Test exporting all available formats."""
        manager = PublishingManager(output_dir=tmp_path)
        exports = manager.export(sample_final_output)

        assert "markdown" in exports
        assert "json" in exports
        assert "html" in exports
        assert "csv" in exports

    def test_publishing_history_save(self, sample_final_output, tmp_path):
        """Test saving publishing history."""
        manager = PublishingManager(output_dir=tmp_path)

        video_id = sample_final_output.source_video.video_id
        article_slug = sample_final_output.seo.slug

        history = manager.history_manager.get_or_create_history(video_id, article_slug)
        assert history.video_id == video_id
        assert history.article_slug == article_slug

        manager.history_manager.save_history(history)
        loaded = manager.history_manager.load_history(video_id, article_slug)

        assert loaded is not None
        assert loaded.video_id == video_id

    def test_statistics(self, sample_final_output, tmp_path):
        """Test statistics retrieval."""
        manager = PublishingManager(output_dir=tmp_path)
        stats = manager.get_statistics()

        assert "total_articles" in stats
        assert "total_publishes" in stats
        assert "by_platform" in stats
        assert "by_status" in stats


class TestPublishConfig:
    """Test publishing configuration."""

    def test_publish_config_creation(self):
        """Test creating publishing config."""
        config = PublishConfig(
            platform=PublishingPlatform.MEDIUM,
            draft=True,
            tags=["test", "publishing"],
            canonical_url="https://example.com",
        )

        assert config.platform == PublishingPlatform.MEDIUM
        assert config.draft is True
        assert len(config.tags) == 2
        assert config.canonical_url == "https://example.com"

    def test_publish_config_defaults(self):
        """Test default configuration values."""
        config = PublishConfig(platform=PublishingPlatform.MEDIUM)

        assert config.draft is True
        assert config.tags == []
        assert config.notify_subscribers is True
        assert config.canonical_url is None


class TestExportFormats:
    """Test specific export format features."""

    def test_markdown_metadata(self, sample_final_output, tmp_path):
        """Test markdown includes metadata."""
        exporter = MarkdownExporter(output_dir=tmp_path)
        path = exporter.export(sample_final_output)

        content = path.read_text()
        assert "Source: Test Video Title" in content
        assert "Channel: Test Channel" in content
        assert "Video ID: test123" in content

    def test_html_responsive(self, sample_final_output, tmp_path):
        """Test HTML export is responsive."""
        exporter = HTMLExporter(output_dir=tmp_path)
        path = exporter.export(sample_final_output)

        content = path.read_text()
        assert "viewport" in content  # Meta viewport tag
        assert "@media (max-width:" in content  # Media queries

    def test_json_complete_data(self, sample_final_output, tmp_path):
        """Test JSON export contains complete data."""
        exporter = JSONExporter(output_dir=tmp_path)
        path = exporter.export(sample_final_output)

        data = json.loads(path.read_text())
        assert "source_video" in data
        assert "article" in data
        assert "seo" in data
        assert "analysis" in data
        assert "transcript" in data

    def test_csv_structure(self, sample_final_output, tmp_path):
        """Test CSV export has proper structure."""
        exporter = CSVExporter(output_dir=tmp_path)
        path = exporter.export(sample_final_output)

        content = path.read_text()
        lines = content.strip().split('\n')

        assert len(lines) > 1  # Header + content
        assert "Type" in lines[0]
        assert "Content" in lines[0]


class TestErrorHandling:
    """Test error handling in exporters and publishers."""

    def test_invalid_output_dir(self, sample_final_output):
        """Test handling of invalid output directory."""
        manager = PublishingManager(output_dir=Path("/nonexistent/path/that/cannot/exist"))
        # Should create directory automatically
        assert manager.output_dir.parent.exists() or manager.output_dir.exists()

    def test_export_with_missing_seo(self, tmp_path):
        """Test export when SEO is missing."""
        output = FinalOutput(
            source_video=VideoMetadata(
                video_id="test",
                url="https://youtube.com/watch?v=test",
                title="Test",
                channel="Test",
                duration_seconds=600,
            ),
            transcript=TranscriptResult(
                video_id="test",
                title="Test",
                channel="Test",
                duration_seconds=600,
                transcript="Test",
                segments=[],
                source="whisper",
                language="en",
            ),
            analysis=ContentAnalysis(
                main_topic="test",
                subtopics=[],
                key_quotes=[],
                data_points=[],
                suggested_sections=[],
                target_audience="general",
                tone="neutral",
                estimated_reading_time=1,
            ),
            article=Article(
                headline="Test",
                introduction="Test",
                sections=[],
                conclusion="Test",
                markdown="Test",
                word_count=10,
            ),
        )

        exporter = MarkdownExporter(output_dir=tmp_path)
        path = exporter.export(output)

        assert path.exists()
        content = path.read_text()
        assert "Test" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
