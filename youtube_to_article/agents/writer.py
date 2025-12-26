"""Agent 3: Article Writer - Transforms transcript into polished article."""
import logging
from typing import Optional
from huggingface_hub import InferenceClient

from models.schemas import (
    TranscriptResult,
    ContentAnalysis,
    Article,
    ArticleSection
)
from config.settings import PipelineConfig

logger = logging.getLogger(__name__)


class WriterAgent:
    """
    Agent 3: Article Writer

    Transforms analyzed transcript into a polished, readable article:
    - Engaging headline
    - Hook introduction
    - Well-structured body sections
    - Conclusion with takeaways
    - Converts spoken language to written prose
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize the Writer agent.

        Args:
            config: Pipeline configuration with HF token and model selection
        """
        self.config = config
        self.client = InferenceClient(token=config.hf_token)
        self.model = config.writer_model

        logger.info(f"Writer agent initialized with model: {self.model}")

    def _build_writer_prompt(
        self,
        transcript: TranscriptResult,
        analysis: ContentAnalysis
    ) -> str:
        """Build the article writing prompt for the LLM."""
        sections_description = "\n".join([
            f"- {section.title}: {section.description}"
            for section in analysis.suggested_sections
        ])

        return f"""You are a professional content writer converting video content to a polished article.

VIDEO METADATA:
- Title: {transcript.title}
- Channel: {transcript.channel}
- Duration: {transcript.duration_seconds} seconds

CONTENT ANALYSIS:
- Main Topic: {analysis.main_topic}
- Subtopics: {', '.join(analysis.subtopics)}
- Target Audience: {analysis.target_audience}
- Tone: {analysis.tone}
- Reading Time Target: {analysis.estimated_reading_time} minutes

SUGGESTED STRUCTURE:
{sections_description}

FULL TRANSCRIPT:
{transcript.transcript}

Write a comprehensive, engaging article following these requirements:

STRUCTURE:
1. Headline: Create an engaging, SEO-friendly headline (NOT just the video title)
2. Introduction: Write a hook paragraph that draws readers in (avoid "In this article..." openings)
3. Body Sections: Follow the {len(analysis.suggested_sections)} suggested sections above
4. Conclusion: Summarize key takeaways

STYLE REQUIREMENTS:
- Convert spoken language to polished written prose
- Remove verbal fillers ("um", "you know", "like", "so", etc.)
- Transform spoken references ("as I showed you") to written form ("as demonstrated above")
- Preserve important quotes with proper attribution
- Use markdown formatting (headers, bold, lists, etc.)
- Maintain the {analysis.tone} tone
- Target {analysis.estimated_reading_time} minute read (~{analysis.estimated_reading_time * 200} words)

Return the article in proper markdown format with clear section headers (## for main sections)."""

    def run(
        self,
        transcript: TranscriptResult,
        analysis: ContentAnalysis
    ) -> Article:
        """
        Generate article from transcript and analysis.

        Args:
            transcript: Transcript result from Agent 1
            analysis: Content analysis from Agent 2

        Returns:
            Article with generated content

        Raises:
            Exception: If article generation fails
        """
        logger.info(f"Generating article for video: {transcript.video_id}")

        # Build prompt
        prompt = self._build_writer_prompt(transcript, analysis)

        # Call HuggingFace Inference API
        try:
            logger.info(f"Calling {self.model} for article generation...")

            # Calculate max tokens based on estimated reading time
            # ~200 words per minute, ~1.3 tokens per word
            max_tokens = int(analysis.estimated_reading_time * 200 * 1.3) + 500

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content writer specializing in transforming video transcripts into engaging, well-structured articles. Write in a clear, professional style."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=min(max_tokens, 4000),  # Cap at model limit
                temperature=0.7,  # Higher temperature for more creative writing
            )

            # Extract response text (the full article)
            article_markdown = response.choices[0].message.content.strip()

            logger.debug(f"Generated article: {len(article_markdown)} characters")

            # Parse article structure
            article_data = self._parse_article(article_markdown)

            logger.info(
                f"Article generation complete: {article_data.word_count} words, "
                f"{len(article_data.sections)} sections"
            )

            return article_data

        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            raise

    def _parse_article(self, markdown: str) -> Article:
        """
        Parse generated article markdown into structured format.

        Args:
            markdown: Full article in markdown format

        Returns:
            Article object with structured content
        """
        lines = markdown.split('\n')

        headline = ""
        introduction = ""
        sections = []
        conclusion = ""

        current_section = None
        current_content = []

        in_intro = True

        for line in lines:
            line = line.strip()

            # Extract headline (first # or top line before content)
            if line.startswith('# ') and not headline:
                headline = line[2:].strip()
                in_intro = True
                continue

            # Section headers (##)
            if line.startswith('## '):
                # Save previous section if exists
                if current_section:
                    sections.append(ArticleSection(
                        heading=current_section,
                        content='\n'.join(current_content).strip(),
                        word_count=len(' '.join(current_content).split())
                    ))
                    current_content = []

                current_section = line[3:].strip()
                in_intro = False

                # Check if this is conclusion
                if 'conclusion' in current_section.lower() or 'takeaway' in current_section.lower():
                    conclusion = current_section
                    current_section = None

                continue

            # Collect content
            if line:
                if in_intro and not current_section:
                    introduction += line + '\n'
                elif current_section or conclusion:
                    current_content.append(line)

        # Save last section
        if current_section:
            sections.append(ArticleSection(
                heading=current_section,
                content='\n'.join(current_content).strip(),
                word_count=len(' '.join(current_content).split())
            ))
        elif conclusion:
            # Conclusion content
            conclusion = '\n'.join(current_content).strip()

        # Calculate total word count
        total_words = len(markdown.split())

        # If no structured sections found, create one section from all content
        if not sections:
            sections.append(ArticleSection(
                heading="Content",
                content=markdown,
                word_count=total_words
            ))

        return Article(
            headline=headline or "Untitled Article",
            introduction=introduction.strip(),
            sections=sections,
            conclusion=conclusion.strip(),
            markdown=markdown,
            word_count=total_words
        )


def create_writer_agent(config: Optional[PipelineConfig] = None) -> WriterAgent:
    """
    Factory function to create a Writer agent.

    Args:
        config: Pipeline configuration (loads from env if not provided)

    Returns:
        Configured WriterAgent instance
    """
    if config is None:
        from config.settings import get_config
        config = get_config()

    return WriterAgent(config)
