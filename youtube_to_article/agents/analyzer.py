"""Agent 2: Content Analyzer - Analyzes transcript structure and extracts key themes."""
import json
import logging
from typing import Optional
from huggingface_hub import InferenceClient

from models.schemas import (
    TranscriptResult,
    ContentAnalysis,
    Quote,
    SectionOutline
)
from config.settings import PipelineConfig

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """
    Agent 2: Content Analyzer

    Analyzes video transcript to extract:
    - Main topic and subtopics
    - Key quotes with timestamps
    - Data points and statistics
    - Suggested article structure
    - Target audience and tone
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize the Analyzer agent.

        Args:
            config: Pipeline configuration with HF token and model selection
        """
        self.config = config
        self.client = InferenceClient(token=config.hf_token)
        self.model = config.analyzer_model

        logger.info(f"Analyzer agent initialized with model: {self.model}")

    def _build_analysis_prompt(self, transcript: TranscriptResult) -> str:
        """Build the analysis prompt for the LLM."""
        return f"""Analyze this YouTube video transcript for article conversion.

VIDEO METADATA:
- Title: {transcript.title}
- Channel: {transcript.channel}
- Duration: {transcript.duration_seconds} seconds
- Language: {transcript.language}

TRANSCRIPT:
{transcript.transcript}

Extract the following information and return as JSON:

1. main_topic: One sentence describing the main topic
2. subtopics: Array of 3-5 key subtopics or themes
3. key_quotes: Array of important quotes (max 5) with format:
   {{"text": "quote text", "timestamp": seconds, "context": "brief context"}}
4. data_points: Array of statistics or data points mentioned
5. suggested_sections: Array of 4-6 logical sections with format:
   {{"title": "section title", "description": "what to cover", "start_time": seconds, "end_time": seconds}}
6. target_audience: Inferred target audience
7. tone: Content tone (e.g., "educational", "entertainment", "technical")
8. estimated_reading_time: Estimated article reading time in minutes

Return ONLY valid JSON, no additional text."""

    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response, handling various formats."""
        # Try to extract JSON from response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            raise ValueError(f"LLM returned invalid JSON: {e}")

    def run(self, transcript: TranscriptResult) -> ContentAnalysis:
        """
        Analyze transcript and extract content structure.

        Args:
            transcript: Transcript result from Agent 1

        Returns:
            ContentAnalysis with extracted information

        Raises:
            Exception: If analysis fails
        """
        logger.info(f"Analyzing transcript for video: {transcript.video_id}")

        # Build prompt
        prompt = self._build_analysis_prompt(transcript)

        # Call HuggingFace Inference API
        try:
            logger.info(f"Calling {self.model} for content analysis...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst. Analyze video transcripts and extract key information for article conversion. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more consistent output
            )

            # Extract response text
            response_text = response.choices[0].message.content

            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON response
            analysis_data = self._parse_llm_response(response_text)

            # Convert to Pydantic models
            key_quotes = [
                Quote(**quote) for quote in analysis_data.get('key_quotes', [])
            ]

            suggested_sections = [
                SectionOutline(**section)
                for section in analysis_data.get('suggested_sections', [])
            ]

            # Build ContentAnalysis object
            analysis = ContentAnalysis(
                main_topic=analysis_data.get('main_topic', 'Unknown topic'),
                subtopics=analysis_data.get('subtopics', []),
                key_quotes=key_quotes,
                data_points=analysis_data.get('data_points', []),
                suggested_sections=suggested_sections,
                target_audience=analysis_data.get('target_audience', 'General audience'),
                tone=analysis_data.get('tone', 'informative'),
                estimated_reading_time=analysis_data.get('estimated_reading_time', 5)
            )

            logger.info(
                f"Analysis complete: {len(analysis.subtopics)} subtopics, "
                f"{len(analysis.key_quotes)} quotes, "
                f"{len(analysis.suggested_sections)} sections"
            )

            return analysis

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise


def create_analyzer_agent(config: Optional[PipelineConfig] = None) -> AnalyzerAgent:
    """
    Factory function to create an Analyzer agent.

    Args:
        config: Pipeline configuration (loads from env if not provided)

    Returns:
        Configured AnalyzerAgent instance
    """
    if config is None:
        from config.settings import get_config
        config = get_config()

    return AnalyzerAgent(config)
