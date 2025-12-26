"""Medium platform publisher."""
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from youtube_to_article.models.schemas import FinalOutput
from .base import BasePublisher, PublishConfig, PublishingResult, PublishingStatus, PublishingPlatform


class MediumPublisher(BasePublisher):
    """Publish articles to Medium platform."""

    MEDIUM_API_URL = "https://api.medium.com/v1"
    MEDIUM_API_TIMEOUT = 30

    def __init__(self, api_token: str):
        """Initialize Medium publisher.

        Args:
            api_token: Medium API access token.
        """
        super().__init__(api_token)
        self.platform = PublishingPlatform.MEDIUM
        self.base_url = self.MEDIUM_API_URL
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def publish(self, final_output: FinalOutput, config: PublishConfig) -> PublishingResult:
        """Publish article to Medium.

        Args:
            final_output: Complete pipeline output.
            config: Publishing configuration.

        Returns:
            Publishing result with Medium article URL.
        """
        try:
            # Validate configuration
            self._validate_config(config)

            # Get user information
            user_id = self._get_user_id()
            if not user_id:
                raise ValueError("Failed to retrieve Medium user ID")

            # Prepare article content
            article_data = self._prepare_article_data(final_output, config)

            # Create article
            response = self._create_article(user_id, article_data)

            if response.status_code not in (200, 201):
                error_msg = self._extract_error_message(response)
                return PublishingResult(
                    platform=PublishingPlatform.MEDIUM,
                    status=PublishingStatus.FAILED,
                    error=error_msg,
                )

            # Parse response
            article_data = response.json().get("data", {})
            article_url = article_data.get("url", "")
            article_id = article_data.get("id", "")

            return PublishingResult(
                platform=PublishingPlatform.MEDIUM,
                status=PublishingStatus.DRAFT if config.draft else PublishingStatus.PUBLISHED,
                url=article_url,
                article_id=article_id,
                metadata={
                    "medium_user_id": user_id,
                    "publication_id": article_data.get("publication", {}).get("id"),
                    "created_at": article_data.get("createdAt"),
                },
            )

        except Exception as e:
            return PublishingResult(
                platform=PublishingPlatform.MEDIUM,
                status=PublishingStatus.FAILED,
                error=str(e),
            )

    def _get_user_id(self) -> Optional[str]:
        """Get authenticated user ID from Medium.

        Returns:
            User ID or None if failed.
        """
        try:
            response = requests.get(
                urljoin(self.base_url, "/me"),
                headers=self.headers,
                timeout=self.MEDIUM_API_TIMEOUT,
            )

            if response.status_code == 200:
                return response.json().get("data", {}).get("id")
            return None

        except Exception:
            return None

    def _prepare_article_data(self, final_output: FinalOutput, config: PublishConfig) -> Dict[str, Any]:
        """Prepare article data for Medium API.

        Args:
            final_output: Pipeline output.
            config: Publishing configuration.

        Returns:
            Article data dictionary for Medium API.
        """
        # Build article content in HTML/Markdown format
        content = self._build_medium_content(final_output)

        # Prepare tags
        tags = config.tags.copy()
        if final_output.seo and final_output.seo.secondary_keywords:
            tags.extend(final_output.seo.secondary_keywords[:3])  # Add up to 3 keywords as tags
        tags = tags[:5]  # Medium allows max 5 tags

        article_data = {
            "title": final_output.article.headline,
            "contentFormat": "html",
            "content": content,
            "tags": tags,
            "notifyFollowers": config.notify_subscribers,
            "publishStatus": "draft" if config.draft else "public",
        }

        # Add canonical URL if provided
        if config.canonical_url:
            article_data["canonicalUrl"] = config.canonical_url
        elif final_output.source_video:
            article_data["canonicalUrl"] = final_output.source_video.url

        return article_data

    def _build_medium_content(self, final_output: FinalOutput) -> str:
        """Build HTML content for Medium article.

        Args:
            final_output: Pipeline output.

        Returns:
            HTML formatted content.
        """
        lines = []

        # Add introduction
        lines.append(f"<p>{final_output.article.introduction}</p>")

        # Add sections
        for section in final_output.article.sections:
            lines.append(f"<h2>{section.heading}</h2>")
            lines.append(f"<p>{section.content}</p>")

        # Add conclusion
        lines.append("<h2>Conclusion</h2>")
        lines.append(f"<p>{final_output.article.conclusion}</p>")

        # Add source attribution
        if final_output.source_video:
            lines.append(
                f'<hr><p><small>Originally from video: <a href="{final_output.source_video.url}">{final_output.source_video.title}</a> '
                f'on {final_output.source_video.channel}</small></p>'
            )

        return "\n".join(lines)

    def _create_article(self, user_id: str, article_data: Dict[str, Any]) -> requests.Response:
        """Create article on Medium.

        Args:
            user_id: Medium user ID.
            article_data: Article data to publish.

        Returns:
            API response.
        """
        import json

        url = urljoin(self.base_url, f"/users/{user_id}/posts")

        return requests.post(
            url,
            json=article_data,
            headers=self.headers,
            timeout=self.MEDIUM_API_TIMEOUT,
        )

    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from API response.

        Args:
            response: API response.

        Returns:
            Error message.
        """
        try:
            data = response.json()
            errors = data.get("errors", [])
            if errors:
                return errors[0].get("message", "Unknown error")
            return data.get("message", f"HTTP {response.status_code}")
        except Exception:
            return f"HTTP {response.status_code}: {response.text[:200]}"
