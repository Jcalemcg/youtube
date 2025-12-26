"""Base publisher class for multi-platform publishing."""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from youtube_to_article.models.schemas import FinalOutput


class PublishingStatus(str, Enum):
    """Publishing status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class PublishingPlatform(str, Enum):
    """Publishing platform enumeration."""

    MEDIUM = "medium"
    DEVTO = "devto"
    HASHNODE = "hashnode"


class PublishConfig(BaseModel):
    """Publishing configuration."""

    platform: PublishingPlatform = Field(description="Target publishing platform")
    draft: bool = Field(default=True, description="Publish as draft (not live)")
    tags: List[str] = Field(default_factory=list, description="Article tags")
    canonical_url: Optional[str] = Field(default=None, description="Canonical URL for SEO")
    schedule_time: Optional[datetime] = Field(default=None, description="Scheduled publish time")
    license: Optional[str] = Field(default=None, description="Content license")
    notify_subscribers: bool = Field(default=True, description="Notify platform subscribers")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")


class PublishingResult(BaseModel):
    """Result of publishing attempt."""

    platform: PublishingPlatform = Field(description="Platform where published")
    status: PublishingStatus = Field(description="Publishing status")
    url: Optional[str] = Field(default=None, description="Published article URL")
    article_id: Optional[str] = Field(default=None, description="Article ID on platform")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Publishing timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BasePublisher(ABC):
    """Abstract base class for article publishers."""

    def __init__(self, api_token: str):
        """Initialize publisher.

        Args:
            api_token: API authentication token.
        """
        self.api_token = api_token
        self.platform = PublishingPlatform.MEDIUM

    @abstractmethod
    def publish(self, final_output: FinalOutput, config: PublishConfig) -> PublishingResult:
        """Publish article to platform.

        Args:
            final_output: Complete pipeline output.
            config: Publishing configuration.

        Returns:
            Publishing result with status and URL.
        """
        pass

    def _extract_text_content(self, html_content: str) -> str:
        """Extract plain text from HTML content.

        Args:
            html_content: HTML content.

        Returns:
            Plain text content.
        """
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)
        # Decode HTML entities
        import html

        text = html.unescape(text)
        return text

    def _validate_config(self, config: PublishConfig) -> None:
        """Validate publishing configuration.

        Args:
            config: Publishing configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not config.platform:
            raise ValueError("Platform is required")

        if config.schedule_time and config.schedule_time < datetime.now():
            raise ValueError("Schedule time cannot be in the past")
