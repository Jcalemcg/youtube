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
from agents.content_filter import ContentFilterAgent
from models.schemas import (
    TranscriptResult,
    ContentAnalysis,
    ArticleTheme,
    Article,
    SEOPackage,
    VideoMetadata,
    FinalOutput,
    QualityAssessment,
    ContentFilterResult
)
from progress import ProgressTracker, create_progress_tracker

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

    def __init__(self, config: Optional[PipelineConfig] = None, progress_tracker: Optional[ProgressTracker] = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration (loads from env if not provided)
            progress_tracker: Optional ProgressTracker for real-time feedback (creates new if not provided)
        """
        if config is None:
            config = get_config()

        self.config = config
        self.progress_tracker = progress_tracker or create_progress_tracker(max_stages=9)

        # Initialize agents
        logger.info("Initializing pipeline agents...")
        self.transcriber = TranscriberAgent(config)
        self.content_filter = ContentFilterAgent()
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

        self.progress_tracker.start_stage(0, "transcription")

        try:
            # Check for cancellation
            if self.progress_tracker.is_cancelled():
                raise RuntimeError("Pipeline execution cancelled by user")

            self.progress_tracker.update(
                step="fetching_metadata",
                message="Extracting video ID and fetching metadata...",
                progress=0.1
            )

            # Check for cancellation
            if self.progress_tracker.is_cancelled():
                raise RuntimeError("Pipeline execution cancelled by user")

            self.progress_tracker.update(
                step="extracting_transcript",
                message="Extracting transcript from video...",
                progress=0.3
            )

            result = self.transcriber.run(youtube_url, force_whisper=force_whisper)

            self.progress_tracker.update(
                step="processing_segments",
                message=f"Processing {len(result.segments)} transcript segments...",
                progress=0.9
            )

            self.progress_tracker.step(
                step="complete",
                message=f"✓ Transcription complete: {len(result.segments)} segments extracted",
                details={
                    "segments": len(result.segments),
                    "title": result.title,
                    "duration": result.duration_seconds
                }
            )

            self.progress_tracker.complete_stage("transcription")
            logger.info(f"✓ Stage 1 complete: {len(result.segments)} segments transcribed")
            return result

        except Exception as e:
            logger.error(f"Error in stage 1 transcription: {e}", exc_info=True)
            self.progress_tracker.error(
                step="transcription_failed",
                message="Transcription failed",
                error_msg=str(e)
            )
            raise

    def stage1_5_filter(self, transcript: TranscriptResult) -> ContentFilterResult:
        """
        Stage 1.5: Filter content for policy compliance and quality issues.

        Args:
            transcript: Transcript from Stage 1

        Returns:
            ContentFilterResult
        """
        logger.info("=" * 60)
        logger.info("STAGE 1.5: CONTENT FILTERING")
        logger.info("=" * 60)

        self.progress_tracker.start_stage(1, "content_filtering")

        try:
            self.progress_tracker.update(
                step="analyzing_content",
                message="Analyzing content for policy compliance...",
                progress=0.3
            )

            result = self.content_filter.filter_transcript(transcript)

            self.progress_tracker.update(
                step="checking_compliance",
                message="Checking compliance and quality metrics...",
                progress=0.7
            )

            self.progress_tracker.step(
                step="complete",
                message=f"✓ Content filtering complete: Status '{result.overall_compliance}'",
                details={
                    "compliance_status": result.overall_compliance,
                    "issues_detected": len(result.flags),
                    "promotional_score": f"{result.promotional_score:.1%}"
                }
            )

            self.progress_tracker.complete_stage("content_filtering")
            logger.info(f"✓ Stage 1.5 complete: Compliance status '{result.overall_compliance}'")
            if result.flags:
                logger.info(f"  {len(result.flags)} issue(s) detected")
            logger.info(f"  Promotional score: {result.promotional_score:.1%}")
            return result

        except Exception as e:
            logger.error(f"Error in stage 1.5 content filtering: {e}", exc_info=True)
            self.progress_tracker.error(
                step="filtering_failed",
                message="Content filtering failed",
                error_msg=str(e)
            )
            raise

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

        self.progress_tracker.start_stage(2, "content_analysis")

        try:
            self.progress_tracker.update(
                step="identifying_topics",
                message="Identifying key topics and themes...",
                progress=0.2
            )

            self.progress_tracker.update(
                step="structuring_content",
                message="Analyzing content structure and sections...",
                progress=0.5
            )

            result = self.analyzer.run(transcript)

            self.progress_tracker.update(
                step="generating_metadata",
                message="Generating analysis metadata...",
                progress=0.9
            )

            self.progress_tracker.step(
                step="complete",
                message=f"✓ Content analysis complete: {len(result.suggested_sections)} sections identified",
                details={
                    "sections": len(result.suggested_sections),
                    "main_topic": result.main_topic,
                    "key_themes": len(result.key_themes)
                }
            )

            self.progress_tracker.complete_stage("content_analysis")
            logger.info(f"✓ Stage 2 complete: {len(result.suggested_sections)} sections identified")
            return result

        except Exception as e:
            logger.error(f"Error in stage 2 content analysis: {e}", exc_info=True)
            self.progress_tracker.error(
                step="analysis_failed",
                message="Content analysis failed",
                error_msg=str(e)
            )
            raise

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

        self.progress_tracker.start_stage(3, "article_writing")

        try:
            self.progress_tracker.update(
                step="generating_structure",
                message="Creating article structure and outline...",
                progress=0.1
            )

            self.progress_tracker.update(
                step="writing_content",
                message="Writing article content and sections...",
                progress=0.5
            )

            result = self.writer.run(transcript, analysis, theme=None)

            self.progress_tracker.update(
                step="formatting",
                message="Formatting article with metadata...",
                progress=0.9
            )

            self.progress_tracker.step(
                step="complete",
                message=f"✓ Article writing complete: {result.word_count} words",
                details={
                    "word_count": result.word_count,
                    "sections": len(result.sections),
                    "title": result.title
                }
            )

            self.progress_tracker.complete_stage("article_writing")
            logger.info(f"✓ Stage 3 complete: {result.word_count} words written")
            return result

        except Exception as e:
            logger.error(f"Error in stage 3 article writing: {e}", exc_info=True)
            self.progress_tracker.error(
                step="writing_failed",
                message="Article writing failed",
                error_msg=str(e)
            )
            raise

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

        self.progress_tracker.start_stage(4, "article_generation")

        try:
            self.progress_tracker.update(
                step="personalizing_theme",
                message=f"Personalizing theme: {theme.theme_style}, Audience: {theme.target_audience}...",
                progress=0.1
            )

            self.progress_tracker.update(
                step="writing_with_theme",
                message="Writing article with theme preferences...",
                progress=0.5
            )

            result = self.writer.run(transcript, analysis, theme=theme)

            self.progress_tracker.update(
                step="finalizing_article",
                message="Finalizing article content...",
                progress=0.9
            )

            self.progress_tracker.step(
                step="complete",
                message=f"✓ Article generation complete: {result.word_count} words",
                details={
                    "word_count": result.word_count,
                    "theme": theme.theme_style,
                    "audience": theme.target_audience,
                    "length": theme.article_length
                }
            )

            self.progress_tracker.complete_stage("article_generation")
            logger.info(f"✓ Stage 4 complete: {result.word_count} words written")
            return result

        except Exception as e:
            logger.error(f"Error in stage 4 article generation: {e}", exc_info=True)
            self.progress_tracker.error(
                step="generation_failed",
                message="Article generation failed",
                error_msg=str(e)
            )
            raise

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

        self.progress_tracker.start_stage(5, "seo_optimization")

        try:
            self.progress_tracker.update(
                step="generating_keywords",
                message="Generating SEO keywords and target phrases...",
                progress=0.2
            )

            self.progress_tracker.update(
                step="optimizing_metadata",
                message="Optimizing meta tags and descriptions...",
                progress=0.5
            )

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

            self.progress_tracker.update(
                step="generating_content",
                message="Generating social media and promotional content...",
                progress=0.9
            )

            self.progress_tracker.step(
                step="complete",
                message="✓ SEO optimization complete: Package generated",
                details={
                    "keywords": len(result.keywords),
                    "meta_tags": len(result.meta_tags) if result.meta_tags else 0
                }
            )

            self.progress_tracker.complete_stage("seo_optimization")
            logger.info(f"✓ Stage 4 complete: SEO package generated")
            return result

        except Exception as e:
            logger.error(f"Error in stage 4 SEO optimization: {e}", exc_info=True)
            self.progress_tracker.error(
                step="seo_failed",
                message="SEO optimization failed",
                error_msg=str(e)
            )
            raise

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

        self.progress_tracker.start_stage(6, "quality_assessment")

        try:
            self.progress_tracker.update(
                step="analyzing_readability",
                message="Analyzing article readability and clarity...",
                progress=0.2
            )

            self.progress_tracker.update(
                step="checking_structure",
                message="Checking content structure and coherence...",
                progress=0.5
            )

            result = self.qa.assess_quality(article, analysis, seo)

            self.progress_tracker.update(
                step="generating_recommendations",
                message="Generating improvement recommendations...",
                progress=0.9
            )

            self.progress_tracker.step(
                step="complete",
                message=f"✓ Quality assessment complete: {result.quality_rating.upper()} ({result.overall_score:.1f}/100)",
                details={
                    "quality_rating": result.quality_rating,
                    "overall_score": result.overall_score,
                    "recommendations": len(result.recommendations) if result.recommendations else 0
                }
            )

            self.progress_tracker.complete_stage("quality_assessment")
            logger.info(f"✓ Stage 5 complete: Quality {result.quality_rating.upper()} ({result.overall_score:.1f}/100)")
            if result.recommendations:
                logger.info(f"  {len(result.recommendations)} recommendations generated")
            return result

        except Exception as e:
            logger.error(f"Error in stage 5 quality assessment: {e}", exc_info=True)
            self.progress_tracker.error(
                step="quality_assessment_failed",
                message="Quality assessment failed",
                error_msg=str(e)
            )
            raise

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

        # Stage 1.5: Content Filtering
        content_filter_result = self.stage1_5_filter(transcript)

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
            content_filter=content_filter_result,
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
        logger.info(f"✓ Content Filter: {content_filter_result.overall_compliance.upper()}")
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

        # Save content filter results
        if output.content_filter:
            filter_path = video_dir / "content_filter.json"
            with open(filter_path, 'w', encoding='utf-8') as f:
                json.dump(output.content_filter.model_dump(), f, indent=2, default=str)

        # Save quality assessment
        if output.quality_assessment:
            qa_path = video_dir / "quality_assessment.json"
            with open(qa_path, 'w', encoding='utf-8') as f:
                json.dump(output.quality_assessment.model_dump(), f, indent=2, default=str)

        logger.info(f"Output saved to: {video_dir}")

        return video_dir

    def get_progress_tracker(self) -> ProgressTracker:
        """
        Get the pipeline's progress tracker.

        Returns:
            ProgressTracker instance
        """
        return self.progress_tracker


def create_pipeline(
    config: Optional[PipelineConfig] = None,
    progress_tracker: Optional[ProgressTracker] = None
) -> YouTubeToArticlePipeline:
    """
    Factory function to create a pipeline.

    Args:
        config: Pipeline configuration (loads from env if not provided)
        progress_tracker: Optional ProgressTracker for real-time feedback

    Returns:
        Configured YouTubeToArticlePipeline instance
    """
    return YouTubeToArticlePipeline(config, progress_tracker)
