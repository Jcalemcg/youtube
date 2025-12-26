"""Pydantic models for data flow between agents."""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


# ============================================================================
# Agent 1: Transcriber Output
# ============================================================================

class TranscriptSegment(BaseModel):
    """Individual transcript segment with timing."""
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    text: str = Field(description="Transcript text for this segment")
    confidence: Optional[float] = Field(default=None, description="Confidence score (0-1) if available")


class TranscriptResult(BaseModel):
    """Complete transcript with metadata."""
    video_id: str = Field(description="YouTube video ID")
    title: str = Field(description="Video title")
    channel: str = Field(description="Channel name")
    duration_seconds: int = Field(description="Video duration in seconds")
    transcript: str = Field(description="Full transcript as plain text")
    segments: List[TranscriptSegment] = Field(description="Timestamped segments")
    source: Literal["captions", "whisper"] = Field(description="Source of transcript")
    language: str = Field(description="Detected or specified language code")
    thumbnail_url: Optional[str] = Field(default=None, description="Video thumbnail URL")
    upload_date: Optional[str] = Field(default=None, description="Video upload date")


# ============================================================================
# Agent 2: Content Analyzer Output
# ============================================================================

class Quote(BaseModel):
    """Important quote from the video."""
    text: str = Field(description="Quote text")
    timestamp: float = Field(description="When the quote appears (seconds)")
    context: Optional[str] = Field(default=None, description="Surrounding context")


class SectionOutline(BaseModel):
    """Suggested article section."""
    title: str = Field(description="Section heading")
    description: str = Field(description="What this section should cover")
    start_time: Optional[float] = Field(default=None, description="Video timestamp where this content starts")
    end_time: Optional[float] = Field(default=None, description="Video timestamp where this content ends")


class ContentAnalysis(BaseModel):
    """Analyzed content structure."""
    main_topic: str = Field(description="Main topic in one sentence")
    subtopics: List[str] = Field(description="3-5 key subtopics/themes")
    key_quotes: List[Quote] = Field(description="Important quotes worth preserving")
    data_points: List[str] = Field(description="Statistics or data points mentioned")
    suggested_sections: List[SectionOutline] = Field(description="4-6 logical sections for article")
    target_audience: str = Field(description="Inferred target audience")
    tone: str = Field(description="Content tone (educational, entertainment, technical, etc.)")
    estimated_reading_time: int = Field(description="Estimated reading time in minutes")
    content_flags: List[str] = Field(default_factory=list, description="List of policy or quality flags identified")


# ============================================================================
# Stage 2.5: Article Theme Selection
# ============================================================================

class ArticleTheme(BaseModel):
    """User-selected article theme and style preferences."""
    theme_style: Literal["professional", "casual", "news", "how-to", "opinion"] = Field(
        description="Overall article style/tone",
        default="professional"
    )
    target_audience: Literal["expert", "beginner", "general"] = Field(
        description="Target audience level",
        default="general"
    )
    article_length: Literal["concise", "standard", "comprehensive"] = Field(
        description="Article length preference",
        default="standard"
    )
    tone_adjustment: Literal["creative", "neutral", "formal"] = Field(
        description="Fine-tune the tone",
        default="neutral"
    )
    visual_preference: Literal["balanced", "code-heavy", "minimal"] = Field(
        description="Preference for visual elements and code blocks",
        default="balanced"
    )
    use_examples: bool = Field(
        description="Include practical examples and case studies",
        default=True
    )
    include_quotes: bool = Field(
        description="Include relevant quotes from the video",
        default=True
    )
    custom_focus: Optional[str] = Field(
        default=None,
        description="Additional focus areas or customization notes"
    )


# ============================================================================
# Agent 3: Article Writer Output
# ============================================================================

class ArticleSection(BaseModel):
    """Individual article section."""
    heading: str = Field(description="Section heading")
    content: str = Field(description="Section content in Markdown")
    word_count: int = Field(description="Word count for this section")


class Article(BaseModel):
    """Generated article."""
    headline: str = Field(description="Article headline")
    introduction: str = Field(description="Introduction paragraph")
    sections: List[ArticleSection] = Field(description="Body sections")
    conclusion: str = Field(description="Conclusion with key takeaways")
    markdown: str = Field(description="Complete article in Markdown format")
    word_count: int = Field(description="Total word count")


# ============================================================================
# Agent 4: SEO Optimizer Output
# ============================================================================

class SocialPosts(BaseModel):
    """Social media post variants."""
    twitter: str = Field(description="Twitter/X post (280 chars)")
    linkedin: str = Field(description="LinkedIn post")
    facebook: Optional[str] = Field(default=None, description="Facebook post")


class SEOPackage(BaseModel):
    """SEO optimization package."""
    meta_title: str = Field(description="Meta title (50-60 chars)")
    meta_description: str = Field(description="Meta description (150-160 chars)")
    slug: str = Field(description="URL slug")
    primary_keyword: str = Field(description="Primary keyword")
    secondary_keywords: List[str] = Field(description="3-5 secondary keywords")
    schema_markup: dict = Field(description="Schema.org Article markup")
    open_graph: dict = Field(description="Open Graph tags")
    twitter_card: dict = Field(description="Twitter Card data")
    social_posts: SocialPosts = Field(description="Social media post variants")
    internal_link_suggestions: List[str] = Field(description="Suggested internal link anchor texts")


# ============================================================================
# Final Pipeline Output
# ============================================================================

class VideoMetadata(BaseModel):
    """Source video metadata."""
    video_id: str
    url: str
    title: str
    channel: str
    duration_seconds: int
    thumbnail_url: Optional[str] = None
    upload_date: Optional[str] = None


# ============================================================================
# Content Filtering and Policy Compliance
# ============================================================================

class ContentPolicyFlag(BaseModel):
    """Flag for policy violation or concerning content."""
    category: Literal["profanity", "violence", "harassment", "hate_speech", "sponsor", "promotional", "misinformation", "spam", "copyright", "other"] = Field(
        description="Category of policy violation"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level of the flag"
    )
    text: str = Field(description="Offending or flagged text snippet (max 200 chars)")
    position: Optional[str] = Field(default=None, description="Position in content (e.g., 'timestamp: 1:23', 'paragraph 3')")
    message: str = Field(description="Human-readable explanation of the flag")
    confidence: float = Field(description="Confidence score (0-1) for this flag", ge=0, le=1)


class ContentFilterResult(BaseModel):
    """Results from content filtering analysis."""
    flags: List[ContentPolicyFlag] = Field(description="List of detected policy violations")
    has_critical_issues: bool = Field(description="Whether any critical issues were found")
    overall_compliance: Literal["compliant", "warning", "flagged", "blocked"] = Field(
        description="Overall compliance status"
    )
    summary: str = Field(description="Summary of filtering results")
    is_sponsor_content: bool = Field(description="Whether content is sponsored")
    sponsor_mentions: List[str] = Field(description="List of sponsor/brand mentions detected")
    promotional_score: float = Field(description="Score 0-1 indicating promotional content level", ge=0, le=1)
    quality_issues: List[str] = Field(description="Non-policy quality issues detected")


# ============================================================================
# Quality Assurance Scoring
# ============================================================================

class ContentQualityScore(BaseModel):
    """Content quality metrics."""
    readability_score: float = Field(description="Readability score (0-100)", ge=0, le=100)
    coherence_score: float = Field(description="Content coherence (0-100)", ge=0, le=100)
    completeness_score: float = Field(description="Content completeness (0-100)", ge=0, le=100)
    relevance_score: float = Field(description="Relevance to main topic (0-100)", ge=0, le=100)
    uniqueness_score: float = Field(description="Originality/uniqueness (0-100)", ge=0, le=100)
    average_score: float = Field(description="Average of all content scores (0-100)", ge=0, le=100)


class SEOQualityScore(BaseModel):
    """SEO quality metrics."""
    keyword_optimization: float = Field(description="Keyword placement and density (0-100)", ge=0, le=100)
    meta_tag_quality: float = Field(description="Quality of meta tags (0-100)", ge=0, le=100)
    slug_quality: float = Field(description="Slug format and relevance (0-100)", ge=0, le=100)
    schema_markup_quality: float = Field(description="Schema markup completeness (0-100)", ge=0, le=100)
    social_media_optimization: float = Field(description="Social media metadata (0-100)", ge=0, le=100)
    average_score: float = Field(description="Average of all SEO scores (0-100)", ge=0, le=100)


class ContentPolicyScore(BaseModel):
    """Content policy compliance metrics."""
    profanity_free_score: float = Field(description="Freedom from profanity (0-100)", ge=0, le=100)
    violence_free_score: float = Field(description="Freedom from violent content (0-100)", ge=0, le=100)
    harassment_free_score: float = Field(description="Freedom from harassment content (0-100)", ge=0, le=100)
    hate_speech_free_score: float = Field(description="Freedom from hate speech (0-100)", ge=0, le=100)
    promotional_content_score: float = Field(description="Score for handling promotional content (0-100)", ge=0, le=100)
    sponsor_transparency_score: float = Field(description="Transparency about sponsorships (0-100)", ge=0, le=100)
    misinformation_free_score: float = Field(description="Freedom from misinformation (0-100)", ge=0, le=100)
    overall_policy_compliance: float = Field(description="Overall compliance score (0-100)", ge=0, le=100)
    policy_rating: Literal["compliant", "warning", "flagged", "blocked"] = Field(description="Policy compliance rating")


class StructureCheck(BaseModel):
    """Article structure validation."""
    has_headline: bool = Field(description="Article has a headline")
    has_introduction: bool = Field(description="Has introduction section")
    has_sections: bool = Field(description="Has body sections")
    has_conclusion: bool = Field(description="Has conclusion section")
    min_word_count_met: bool = Field(description="Meets minimum word count (200 words)")
    sections_have_content: bool = Field(description="All sections have meaningful content")
    proper_formatting: bool = Field(description="Uses proper Markdown formatting")
    all_checks_passed: bool = Field(description="All structure checks passed")
    passed_checks: int = Field(description="Number of checks passed")
    total_checks: int = Field(description="Total number of structure checks")


class QualityRecommendation(BaseModel):
    """Suggestion for quality improvement."""
    category: Literal["content", "seo", "structure", "style"] = Field(description="Recommendation category")
    severity: Literal["info", "warning", "critical"] = Field(description="Severity level")
    message: str = Field(description="Recommendation message")
    action: Optional[str] = Field(default=None, description="Suggested action to take")


class QualityAssessment(BaseModel):
    """Comprehensive quality assessment."""
    content_quality: ContentQualityScore = Field(description="Content quality metrics")
    seo_quality: SEOQualityScore = Field(description="SEO quality metrics")
    structure_check: StructureCheck = Field(description="Structure validation results")
    policy_compliance: Optional[ContentPolicyScore] = Field(default=None, description="Content policy compliance metrics")
    overall_score: float = Field(description="Overall quality score (0-100)", ge=0, le=100)
    quality_rating: Literal["excellent", "good", "fair", "poor"] = Field(description="Quality rating category")
    recommendations: List[QualityRecommendation] = Field(description="Improvement recommendations")
    assessment_timestamp: datetime = Field(default_factory=datetime.now, description="Assessment timestamp")


# ============================================================================
# Final Pipeline Output
# ============================================================================

class VideoMetadata(BaseModel):
    """Source video metadata."""
    video_id: str
    url: str
    title: str
    channel: str
    duration_seconds: int
    thumbnail_url: Optional[str] = None
    upload_date: Optional[str] = None


class FinalOutput(BaseModel):
    """Complete pipeline output."""
    source_video: VideoMetadata = Field(description="Source video information")
    transcript: TranscriptResult = Field(description="Transcript result")
    content_filter: Optional[ContentFilterResult] = Field(default=None, description="Content filtering results")
    analysis: ContentAnalysis = Field(description="Content analysis")
    article: Article = Field(description="Generated article")
    seo: SEOPackage = Field(description="SEO package")
    quality_assessment: Optional[QualityAssessment] = Field(default=None, description="Quality assessment results")
    generated_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    pipeline_version: str = Field(default="1.0.0", description="Pipeline version")

    class Config:
        json_schema_extra = {
            "example": {
                "source_video": {
                    "video_id": "dQw4w9WgXcQ",
                    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                    "title": "Example Video",
                    "channel": "Example Channel",
                    "duration_seconds": 600
                }
            }
        }
