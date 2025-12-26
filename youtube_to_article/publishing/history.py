"""Publishing history tracking."""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from youtube_to_article.publishers.base import PublishingResult


class PublishingHistory(BaseModel):
    """Publishing history record."""

    video_id: str = Field(description="Source video ID")
    article_slug: str = Field(description="Article slug")
    results: List[PublishingResult] = Field(default_factory=list, description="Publishing results")
    created_at: datetime = Field(default_factory=datetime.now, description="When record was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

    def add_result(self, result: PublishingResult) -> None:
        """Add publishing result.

        Args:
            result: Publishing result to add.
        """
        self.results.append(result)
        self.updated_at = datetime.now()


class PublishingHistoryManager:
    """Manage publishing history storage and retrieval."""

    def __init__(self, history_dir: Optional[Path] = None):
        """Initialize history manager.

        Args:
            history_dir: Directory for storing history files.
        """
        self.history_dir = history_dir or Path("./output/publishing_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _get_history_file(self, video_id: str, article_slug: str) -> Path:
        """Get history file path for article.

        Args:
            video_id: Video ID.
            article_slug: Article slug.

        Returns:
            Path to history file.
        """
        filename = f"{video_id}_{article_slug}_history.json"
        return self.history_dir / filename

    def save_history(self, history: PublishingHistory) -> Path:
        """Save publishing history.

        Args:
            history: Publishing history to save.

        Returns:
            Path to saved file.
        """
        filepath = self._get_history_file(history.video_id, history.article_slug)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history.model_dump(mode="json"), f, indent=2, default=str)

        return filepath

    def load_history(self, video_id: str, article_slug: str) -> Optional[PublishingHistory]:
        """Load publishing history.

        Args:
            video_id: Video ID.
            article_slug: Article slug.

        Returns:
            Publishing history or None if not found.
        """
        filepath = self._get_history_file(video_id, article_slug)

        if not filepath.exists():
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return PublishingHistory(**data)
        except Exception:
            return None

    def get_or_create_history(self, video_id: str, article_slug: str) -> PublishingHistory:
        """Get existing history or create new one.

        Args:
            video_id: Video ID.
            article_slug: Article slug.

        Returns:
            Publishing history.
        """
        history = self.load_history(video_id, article_slug)
        if history is None:
            history = PublishingHistory(video_id=video_id, article_slug=article_slug)
        return history

    def list_histories(self) -> List[PublishingHistory]:
        """List all publishing histories.

        Returns:
            List of publishing histories.
        """
        histories = []

        for filepath in self.history_dir.glob("*_history.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    histories.append(PublishingHistory(**data))
            except Exception:
                continue

        return sorted(histories, key=lambda h: h.updated_at, reverse=True)

    def get_statistics(self) -> Dict[str, Any]:
        """Get publishing statistics.

        Returns:
            Statistics dictionary.
        """
        histories = self.list_histories()

        total_articles = len(histories)
        total_publishes = sum(len(h.results) for h in histories)

        platform_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for history in histories:
            for result in history.results:
                platform = result.platform.value
                status = result.status.value

                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_articles": total_articles,
            "total_publishes": total_publishes,
            "by_platform": platform_counts,
            "by_status": status_counts,
        }
