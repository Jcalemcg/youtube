"""Agent 4: SEO Optimizer - Enhances article for search visibility."""
import json
import logging
import re
from typing import Optional
from datetime import datetime
from huggingface_hub import InferenceClient

from models.schemas import (
    Article,
    ContentAnalysis,
    SEOPackage,
    SocialPosts,
    VideoMetadata
)
from config.settings import PipelineConfig

logger = logging.getLogger(__name__)


class SEOAgent:
    """
    Agent 4: SEO Optimizer

    Enhances article for search visibility:
    - Meta title and description
    - URL slug
    - Keywords (primary + secondary)
    - Schema.org markup
    - Open Graph tags
    - Twitter Card data
    - Social media post variants
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize the SEO agent.

        Args:
            config: Pipeline configuration with HF token and model selection
        """
        self.config = config
        self.client = InferenceClient(token=config.hf_token)
        self.model = config.seo_model

        logger.info(f"SEO agent initialized with model: {self.model}")

    def _build_seo_prompt(
        self,
        article: Article,
        analysis: ContentAnalysis,
        video_meta: VideoMetadata
    ) -> str:
        """Build the SEO optimization prompt for the LLM."""
        return f"""Generate SEO metadata for this article converted from a YouTube video.

ARTICLE HEADLINE:
{article.headline}

ARTICLE CONTENT (first 500 chars):
{article.markdown[:500]}...

CONTENT ANALYSIS:
- Main Topic: {analysis.main_topic}
- Subtopics: {', '.join(analysis.subtopics)}
- Target Audience: {analysis.target_audience}

SOURCE VIDEO:
- Title: {video_meta.title}
- Channel: {video_meta.channel}

Generate the following SEO elements and return as JSON:

1. meta_title: SEO-optimized title (50-60 characters, include primary keyword)
2. meta_description: Compelling description (150-160 characters)
3. slug: URL-friendly slug (lowercase, hyphens, no special chars)
4. primary_keyword: Main target keyword phrase
5. secondary_keywords: Array of 3-5 related keywords
6. twitter_post: Engaging tweet (280 characters max)
7. linkedin_post: Professional LinkedIn post (2-3 sentences)
8. internal_link_suggestions: Array of 3-5 potential internal link anchor texts

REQUIREMENTS:
- Meta title must be 50-60 chars
- Meta description must be 150-160 chars
- Slug must be lowercase with hyphens only
- Keywords should be realistic search terms
- Social posts should be engaging and drive clicks

Return ONLY valid JSON, no additional text."""

    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response, handling various formats."""
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

    def _generate_schema_markup(
        self,
        article: Article,
        video_meta: VideoMetadata,
        seo_data: dict
    ) -> dict:
        """Generate Schema.org Article markup."""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.headline,
            "description": seo_data.get('meta_description', ''),
            "author": {
                "@type": "Person",
                "name": video_meta.channel
            },
            "datePublished": video_meta.upload_date or datetime.now().isoformat(),
            "articleBody": article.markdown,
            "wordCount": article.word_count,
            "keywords": [seo_data.get('primary_keyword', '')] + seo_data.get('secondary_keywords', []),
            "thumbnailUrl": video_meta.thumbnail_url,
            "video": {
                "@type": "VideoObject",
                "name": video_meta.title,
                "url": video_meta.url,
                "thumbnailUrl": video_meta.thumbnail_url,
                "uploadDate": video_meta.upload_date
            }
        }

    def _generate_open_graph(
        self,
        article: Article,
        video_meta: VideoMetadata,
        seo_data: dict
    ) -> dict:
        """Generate Open Graph tags."""
        return {
            "og:type": "article",
            "og:title": seo_data.get('meta_title', article.headline),
            "og:description": seo_data.get('meta_description', ''),
            "og:url": f"https://example.com/articles/{seo_data.get('slug', '')}",
            "og:image": video_meta.thumbnail_url or "",
            "og:site_name": "Your Site Name",
            "article:author": video_meta.channel,
            "article:published_time": video_meta.upload_date or datetime.now().isoformat(),
        }

    def _generate_twitter_card(
        self,
        article: Article,
        video_meta: VideoMetadata,
        seo_data: dict
    ) -> dict:
        """Generate Twitter Card tags."""
        return {
            "twitter:card": "summary_large_image",
            "twitter:title": seo_data.get('meta_title', article.headline),
            "twitter:description": seo_data.get('meta_description', ''),
            "twitter:image": video_meta.thumbnail_url or "",
            "twitter:creator": f"@{video_meta.channel}",
        }

    def run(
        self,
        article: Article,
        analysis: ContentAnalysis,
        video_meta: VideoMetadata
    ) -> SEOPackage:
        """
        Generate SEO package for article.

        Args:
            article: Generated article from Agent 3
            analysis: Content analysis from Agent 2
            video_meta: Source video metadata

        Returns:
            SEOPackage with all SEO elements

        Raises:
            Exception: If SEO generation fails
        """
        logger.info("Generating SEO package...")

        # Build prompt
        prompt = self._build_seo_prompt(article, analysis, video_meta)

        # Call HuggingFace Inference API
        try:
            logger.info(f"Calling {self.model} for SEO optimization...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an SEO expert. Generate optimized metadata for articles. Always return valid JSON with all required fields."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            # Extract response
            response_text = response.choices[0].message.content
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON response
            seo_data = self._parse_llm_response(response_text)

            # Validate and clean data
            meta_title = seo_data.get('meta_title', article.headline)[:60]
            meta_description = seo_data.get('meta_description', '')[:160]
            slug = re.sub(r'[^a-z0-9-]', '', seo_data.get('slug', '').lower().replace(' ', '-'))

            # Generate structured data
            schema_markup = self._generate_schema_markup(article, video_meta, seo_data)
            open_graph = self._generate_open_graph(article, video_meta, seo_data)
            twitter_card = self._generate_twitter_card(article, video_meta, seo_data)

            # Build social posts
            social_posts = SocialPosts(
                twitter=seo_data.get('twitter_post', '')[:280],
                linkedin=seo_data.get('linkedin_post', '')
            )

            # Build SEO package
            seo_package = SEOPackage(
                meta_title=meta_title,
                meta_description=meta_description,
                slug=slug,
                primary_keyword=seo_data.get('primary_keyword', ''),
                secondary_keywords=seo_data.get('secondary_keywords', []),
                schema_markup=schema_markup,
                open_graph=open_graph,
                twitter_card=twitter_card,
                social_posts=social_posts,
                internal_link_suggestions=seo_data.get('internal_link_suggestions', [])
            )

            logger.info("SEO package generation complete")

            return seo_package

        except Exception as e:
            logger.error(f"SEO generation failed: {e}")
            raise


def create_seo_agent(config: Optional[PipelineConfig] = None) -> SEOAgent:
    """
    Factory function to create an SEO agent.

    Args:
        config: Pipeline configuration (loads from env if not provided)

    Returns:
        Configured SEOAgent instance
    """
    if config is None:
        from config.settings import get_config
        config = get_config()

    return SEOAgent(config)
