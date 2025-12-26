"""Main pipeline orchestrator for YouTube-to-Article conversion."""
import logging
from datetime import datetime
from typing import Optional

from config.settings import PipelineConfig, get_config
from agents.transcriber import TranscriberAgent
from agents.analyzer import AnalyzerAgent
from agents.writer import WriterAgent
from agents.seo_optimizer import SEOAgent
from agents.quality_assurance import QualityAssuranceAgent
from models.schemas import (
    TranscriptResult,
    ContentAnalysis,
    ArticleTheme,
    Article,
    SEOPackage,
    VideoMetadata,
    FinalOutput,
    QualityAssessment
)

logger = logging.getLogger(__name__)


class YouTubeToArticlePipeline:
    """
    Main pipeline orchestrator.

    Coordinates all 4 agents in sequence:
    1. Transcriber: Extract transcript from YouTube
    2. Analyzer: Analyze content structure
    3. Writer: Generate article
    4. SEO: Add SEO metadata

    Supports both full pipeline and stage-by-stage execution for UI interaction.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration (loads from env if not provided)
        """
        if config is None:
            config = get_config()

        self.config = config

        # Initialize agents
        logger.info("Initializing pipeline agents...")
        self.transcriber = TranscriberAgent(config)
        self.analyzer = AnalyzerAgent(config)
        self.writer = WriterAgent(config)
        self.seo = SEOAgent(config)
        self.qa = QualityAssuranceAgent()

        logger.info("Pipeline initialized successfully")

    # Stage-by-stage methods for UI interaction

    def stage1_transcribe(self, youtube_url: str, force_whisper: bool = False) -> TranscriptResult:
        """
        Stage 1: Extract transcript from YouTube video.

        Args:
            youtube_url: YouTube video URL or ID
            force_whisper: Force Whisper transcription (skip captions)

        Returns:
            TranscriptResult
        """
        logger.info("=" * 60)
        logger.info("STAGE 1: TRANSCRIPTION")
        logger.info("=" * 60)

        result = self.transcriber.run(youtube_url, force_whisper=force_whisper)

        logger.info(f"✓ Stage 1 complete: {len(result.segments)} segments transcribed")
        return result

    def stage2_analyze(self, transcript: TranscriptResult) -> ContentAnalysis:
        """
        Stage 2: Analyze transcript content.

        Args:
            transcript: Transcript from Stage 1

        Returns:
            ContentAnalysis
        """
        logger.info("=" * 60)
        logger.info("STAGE 2: CONTENT ANALYSIS")
        logger.info("=" * 60)

        result = self.analyzer.run(transcript)

        logger.info(f"✓ Stage 2 complete: {len(result.suggested_sections)} sections identified")
        return result

    def stage3_write(
        self,
        transcript: TranscriptResult,
        analysis: ContentAnalysis
    ) -> Article:
        """
        Stage 3: Generate article (legacy method without theme).

        Args:
            transcript: Transcript from Stage 1
            analysis: Analysis from Stage 2

        Returns:
            Article
        """
        logger.info("=" * 60)
        logger.info("STAGE 3: ARTICLE GENERATION")
        logger.info("=" * 60)

        result = self.writer.run(transcript, analysis, theme=None)

        logger.info(f"✓ Stage 3 complete: {result.word_count} words written")
        return result

    def stage4_write(
        self,
        transcript: TranscriptResult,
        analysis: ContentAnalysis,
        theme: ArticleTheme
    ) -> Article:
        """
        Stage 4: Generate article with theme selection.

        Args:
            transcript: Transcript from Stage 1
            analysis: Analysis from Stage 2
            theme: Article theme and style preferences from Stage 2.5

        Returns:
            Article
        """
        logger.info("=" * 60)
        logger.info("STAGE 4: ARTICLE GENERATION (WITH THEME)")
        logger.info("=" * 60)
        logger.info(f"Theme: {theme.theme_style}, Audience: {theme.target_audience}, Length: {theme.article_length}")

        result = self.writer.run(transcript, analysis, theme=theme)

        logger.info(f"✓ Stage 4 complete: {result.word_count} words written")
        return result

    def stage4_optimize_seo(
        self,
        article: Article,
        analysis: ContentAnalysis,
        transcript: TranscriptResult
    ) -> SEOPackage:
        """
        Stage 4: Generate SEO package.

        Args:
            article: Article from Stage 3
            analysis: Analysis from Stage 2
            transcript: Transcript from Stage 1 (for metadata)

        Returns:
            SEOPackage
        """
        logger.info("=" * 60)
        logger.info("STAGE 4: SEO OPTIMIZATION")
        logger.info("=" * 60)

        # Create VideoMetadata from transcript
        video_meta = VideoMetadata(
            video_id=transcript.video_id,
            url=f"https://youtube.com/watch?v={transcript.video_id}",
            title=transcript.title,
            channel=transcript.channel,
            duration_seconds=transcript.duration_seconds,
            thumbnail_url=transcript.thumbnail_url,
            upload_date=transcript.upload_date
        )

        result = self.seo.run(article, analysis, video_meta)

        logger.info(f"✓ Stage 4 complete: SEO package generated")
        return result

    def stage5_assess_quality(
        self,
        article: Article,
        analysis: ContentAnalysis,
        seo: SEOPackage
    ) -> QualityAssessment:
        """
        Stage 5: Assess article quality and provide recommendations.

        Args:
            article: Article from Stage 4
            analysis: Analysis from Stage 2
            seo: SEO package from Stage 4

        Returns:
            QualityAssessment
        """
        logger.info("=" * 60)
        logger.info("STAGE 5: QUALITY ASSESSMENT")
        logger.info("=" * 60)

        result = self.qa.assess_quality(article, analysis, seo)

        logger.info(f"✓ Stage 5 complete: Quality {result.quality_rating.upper()} ({result.overall_score:.1f}/100)")
        if result.recommendations:
            logger.info(f"  {len(result.recommendations)} recommendations generated")
        return result

    # Full pipeline execution

    def process(
        self,
        youtube_url: str,
        force_whisper: bool = False
    ) -> FinalOutput:
        """
        Process entire pipeline from YouTube URL to final article.

        Args:
            youtube_url: YouTube video URL or ID
            force_whisper: Force Whisper transcription (skip captions)

        Returns:
            FinalOutput with all pipeline results
        """
        logger.info("\n" + "=" * 60)
        logger.info("STARTING FULL PIPELINE")
        logger.info(f"Video: {youtube_url}")
        logger.info("=" * 60 + "\n")

        # Stage 1: Transcription
        transcript = self.stage1_transcribe(youtube_url, force_whisper)

        # Stage 2: Analysis
        analysis = self.stage2_analyze(transcript)

        # Stage 3: Article Writing
        article = self.stage3_write(transcript, analysis)

        # Stage 4: SEO Optimization
        seo_package = self.stage4_optimize_seo(article, analysis, transcript)

        # Stage 5: Quality Assessment
        quality_assessment = self.stage5_assess_quality(article, analysis, seo_package)

        # Build video metadata
        video_meta = VideoMetadata(
            video_id=transcript.video_id,
            url=f"https://youtube.com/watch?v={transcript.video_id}",
            title=transcript.title,
            channel=transcript.channel,
            duration_seconds=transcript.duration_seconds,
            thumbnail_url=transcript.thumbnail_url,
            upload_date=transcript.upload_date
        )

        # Build final output
        final_output = FinalOutput(
            source_video=video_meta,
            transcript=transcript,
            analysis=analysis,
            article=article,
            seo=seo_package,
            quality_assessment=quality_assessment,
            generated_at=datetime.now(),
            pipeline_version="1.0.0"
        )

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"✓ Transcript: {len(transcript.segments)} segments")
        logger.info(f"✓ Analysis: {len(analysis.suggested_sections)} sections")
        logger.info(f"✓ Article: {article.word_count} words")
        logger.info(f"✓ SEO: Complete package")
        logger.info(f"✓ Quality: {quality_assessment.quality_rating.upper()} ({quality_assessment.overall_score:.1f}/100)")
        logger.info("=" * 60 + "\n")

        return final_output

    def save_output(self, output: FinalOutput, output_dir: Optional[str] = None):
        """
        Save pipeline output to files.

        Args:
            output: Final pipeline output
            output_dir: Directory to save (uses config default if not provided)
        """
        import json
        from pathlib import Path

        if output_dir is None:
            output_dir = self.config.output_dir

        # Create output directory for this video
        video_dir = Path(output_dir) / output.source_video.video_id
        video_dir.mkdir(parents=True, exist_ok=True)

        # Save complete output as JSON
        complete_path = video_dir / "complete.json"
        with open(complete_path, 'w', encoding='utf-8') as f:
            json.dump(output.model_dump(), f, indent=2, default=str)

        # Save article as Markdown
        article_path = video_dir / "article.md"
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(output.article.markdown)

        # Save transcript as text
        transcript_path = video_dir / "transcript.txt"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(output.transcript.transcript)

        # Save SEO package
        seo_path = video_dir / "seo.json"
        with open(seo_path, 'w', encoding='utf-8') as f:
            json.dump(output.seo.model_dump(), f, indent=2, default=str)

        # Save quality assessment
        if output.quality_assessment:
            qa_path = video_dir / "quality_assessment.json"
            with open(qa_path, 'w', encoding='utf-8') as f:
                json.dump(output.quality_assessment.model_dump(), f, indent=2, default=str)

        logger.info(f"Output saved to: {video_dir}")

        return video_dir


def create_pipeline(config: Optional[PipelineConfig] = None) -> YouTubeToArticlePipeline:
    """
    Factory function to create a pipeline.

    Args:
        config: Pipeline configuration (loads from env if not provided)

    Returns:
        Configured YouTubeToArticlePipeline instance
    """
    return YouTubeToArticlePipeline(config)
