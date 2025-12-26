"""Progress tracking system for real-time step-by-step feedback."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ProgressLevel(str, Enum):
    """Progress event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    STEP = "step"  # Major step completion
    MILESTONE = "milestone"  # Stage completion
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ProgressEvent:
    """Represents a progress update event."""

    timestamp: datetime = field(default_factory=datetime.now)
    stage: str = ""  # Stage name (e.g., "transcribe", "analyze")
    step: str = ""  # Current step (e.g., "extracting_video_id")
    message: str = ""  # User-friendly message
    level: ProgressLevel = ProgressLevel.INFO
    progress: float = 0.0  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    error: Optional[str] = None  # Error message if applicable

    def __str__(self) -> str:
        """Format event as string."""
        if self.error:
            return f"[{self.level.upper()}] {self.stage}/{self.step}: {self.message} - ERROR: {self.error}"

        progress_str = f" ({self.progress:.0%})" if self.progress > 0 else ""
        return f"[{self.level.upper()}] {self.stage}/{self.step}: {self.message}{progress_str}"


class ProgressTracker:
    """Manages progress tracking with callback system for real-time updates."""

    def __init__(self, max_stages: int = 9):
        """
        Initialize progress tracker.

        Args:
            max_stages: Maximum number of stages in pipeline
        """
        self.max_stages = max_stages
        self.current_stage = 0
        self.current_step = ""
        self.start_time = datetime.now()
        self.stage_times: Dict[str, datetime] = {}  # Start time for each stage
        self.step_times: Dict[str, datetime] = {}  # Start time for each step
        self.stage_progress: Dict[int, float] = {}  # Progress per stage
        self.stage_durations: Dict[str, float] = {}  # Actual duration for each completed stage

        # Callbacks
        self._callbacks: List[Callable[[ProgressEvent], None]] = []
        self._error_callbacks: List[Callable[[ProgressEvent], None]] = []

        # Event history
        self.events: List[ProgressEvent] = []

        logger.debug("ProgressTracker initialized")

    def add_callback(self, callback: Callable[[ProgressEvent], None]) -> None:
        """
        Add a callback for progress events.

        Args:
            callback: Function that accepts a ProgressEvent
        """
        self._callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[ProgressEvent], None]) -> None:
        """
        Add a callback for error events.

        Args:
            callback: Function that accepts a ProgressEvent
        """
        self._error_callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ProgressEvent], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _emit(self, event: ProgressEvent) -> None:
        """
        Emit a progress event to all callbacks.

        Args:
            event: Progress event to emit
        """
        # Store in history
        self.events.append(event)

        # Call appropriate callbacks
        if event.error or event.level == ProgressLevel.ERROR:
            for callback in self._error_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")

        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def start_stage(self, stage: int, stage_name: str) -> None:
        """
        Mark the start of a new stage.

        Args:
            stage: Stage number (0-based)
            stage_name: Human-readable stage name
        """
        self.current_stage = stage
        self.current_step = ""
        self.stage_times[stage_name] = datetime.now()

        event = ProgressEvent(
            stage=stage_name,
            step="started",
            message=f"Starting stage: {stage_name}",
            level=ProgressLevel.MILESTONE,
            progress=stage / self.max_stages,
            details={"stage_number": stage, "total_stages": self.max_stages}
        )

        logger.info(str(event))
        self._emit(event)

    def update(
        self,
        step: str,
        message: str,
        progress: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        level: ProgressLevel = ProgressLevel.INFO
    ) -> None:
        """
        Update progress for current stage.

        Args:
            step: Current step identifier
            message: User-friendly progress message
            progress: Progress percentage (0.0 to 1.0) for current stage
            details: Additional metadata
            level: Event severity level
        """
        self.current_step = step
        self.step_times[step] = datetime.now()

        # Calculate overall progress
        overall_progress = (self.current_stage + (progress or 0.0)) / self.max_stages

        event = ProgressEvent(
            stage=f"stage_{self.current_stage}",
            step=step,
            message=message,
            progress=overall_progress,
            level=level,
            details=details or {}
        )

        if level == ProgressLevel.STEP or level == ProgressLevel.INFO:
            logger.info(str(event))
        elif level == ProgressLevel.DEBUG:
            logger.debug(str(event))
        else:
            logger.warning(str(event))

        self._emit(event)

    def step(
        self,
        step: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark a major step completion.

        Args:
            step: Step identifier
            message: Step completion message
            details: Additional metadata
        """
        self.update(
            step=step,
            message=message,
            details=details,
            level=ProgressLevel.STEP
        )

    def complete_stage(self, stage_name: str) -> None:
        """
        Mark stage as complete.

        Args:
            stage_name: Stage name
        """
        elapsed = self._get_elapsed_time(stage_name)
        self.stage_durations[stage_name] = elapsed

        # Estimate remaining time
        estimated_remaining = self._estimate_remaining_time()

        event = ProgressEvent(
            stage=stage_name,
            step="completed",
            message=f"Completed stage: {stage_name}",
            level=ProgressLevel.MILESTONE,
            progress=(self.current_stage + 1) / self.max_stages,
            details={
                "elapsed_seconds": elapsed,
                "estimated_remaining_seconds": estimated_remaining
            }
        )

        logger.info(str(event))
        self._emit(event)

    def error(
        self,
        step: str,
        message: str,
        error_msg: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error event.

        Args:
            step: Step where error occurred
            message: Error description
            error_msg: Error message/traceback
            details: Additional metadata
        """
        event = ProgressEvent(
            stage=f"stage_{self.current_stage}",
            step=step,
            message=message,
            level=ProgressLevel.ERROR,
            error=error_msg,
            details=details or {}
        )

        logger.error(str(event))
        self._emit(event)

    def debug(
        self,
        step: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log debug-level progress information.

        Args:
            step: Step identifier
            message: Debug message
            details: Additional metadata
        """
        self.update(
            step=step,
            message=message,
            details=details,
            level=ProgressLevel.DEBUG
        )

    def _get_elapsed_time(self, stage_name: str) -> float:
        """Get elapsed time for a stage in seconds."""
        if stage_name in self.stage_times:
            return (datetime.now() - self.stage_times[stage_name]).total_seconds()
        return 0.0

    def _estimate_remaining_time(self) -> float:
        """
        Estimate remaining time for entire pipeline in seconds.

        Uses average of completed stages to estimate remaining stages.
        """
        if not self.stage_durations:
            return 0.0

        avg_duration = sum(self.stage_durations.values()) / len(self.stage_durations)
        remaining_stages = self.max_stages - (self.current_stage + 1)
        return avg_duration * remaining_stages

    def get_total_elapsed(self) -> float:
        """Get total elapsed time since tracker start in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def get_estimated_total_time(self) -> float:
        """
        Get estimated total time for entire pipeline in seconds.

        Returns:
            Estimated total duration based on completed stages
        """
        return self.get_total_elapsed() + self._estimate_remaining_time()

    def get_time_estimate(self) -> Dict[str, float]:
        """
        Get comprehensive time estimate information.

        Returns:
            Dictionary with elapsed, remaining, and total estimates
        """
        elapsed = self.get_total_elapsed()
        remaining = self._estimate_remaining_time()
        total = elapsed + remaining

        return {
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
            "total_seconds": total,
            "elapsed_minutes": elapsed / 60,
            "remaining_minutes": remaining / 60,
            "total_minutes": total / 60
        }

    def format_time(self, seconds: float) -> str:
        """
        Format seconds into human-readable time string.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "2m 35s" or "1h 23m")
        """
        if seconds < 0:
            return "N/A"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def get_stage_summary(self) -> Dict[str, Any]:
        """
        Get summary of current progress.

        Returns:
            Dictionary with progress summary
        """
        time_estimates = self.get_time_estimate()

        return {
            "current_stage": self.current_stage,
            "current_step": self.current_step,
            "total_elapsed": self.get_total_elapsed(),
            "total_elapsed_formatted": self.format_time(self.get_total_elapsed()),
            "estimated_remaining": self._estimate_remaining_time(),
            "estimated_remaining_formatted": self.format_time(self._estimate_remaining_time()),
            "estimated_total": self.get_estimated_total_time(),
            "estimated_total_formatted": self.format_time(self.get_estimated_total_time()),
            "events_count": len(self.events),
            "last_event": self.events[-1].timestamp if self.events else None,
            "stage_durations": self.stage_durations
        }

    def reset(self) -> None:
        """Reset tracker to initial state."""
        self.current_stage = 0
        self.current_step = ""
        self.start_time = datetime.now()
        self.stage_times.clear()
        self.step_times.clear()
        self.stage_progress.clear()
        self.stage_durations.clear()
        self.events.clear()
        self._is_cancelled = False
        logger.debug("ProgressTracker reset")

    def cancel(self) -> None:
        """
        Request cancellation of pipeline execution.

        Sets a flag that can be checked by the pipeline to stop processing.
        """
        self._is_cancelled = True
        event = ProgressEvent(
            stage=f"stage_{self.current_stage}",
            step="cancellation_requested",
            message="Cancellation requested by user",
            level=ProgressLevel.WARNING
        )
        logger.warning(str(event))
        self._emit(event)

    def is_cancelled(self) -> bool:
        """
        Check if cancellation has been requested.

        Returns:
            True if cancellation was requested, False otherwise
        """
        return getattr(self, '_is_cancelled', False)


class StageProgressContext:
    """Context manager for tracking a stage's progress."""

    def __init__(
        self,
        tracker: ProgressTracker,
        stage_num: int,
        stage_name: str
    ):
        """
        Initialize context.

        Args:
            tracker: ProgressTracker instance
            stage_num: Stage number (0-based)
            stage_name: Stage name
        """
        self.tracker = tracker
        self.stage_num = stage_num
        self.stage_name = stage_name

    def __enter__(self):
        """Enter context and start stage tracking."""
        self.tracker.start_stage(self.stage_num, self.stage_name)
        return self.tracker

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and complete stage tracking."""
        if exc_type is not None:
            # Error occurred
            self.tracker.error(
                step="stage_error",
                message=f"Error in stage: {self.stage_name}",
                error_msg=str(exc_val),
                details={"exception_type": exc_type.__name__}
            )
        else:
            # Stage completed successfully
            self.tracker.complete_stage(self.stage_name)

        return False  # Don't suppress exceptions


def create_progress_tracker(max_stages: int = 9) -> ProgressTracker:
    """
    Factory function to create a progress tracker.

    Args:
        max_stages: Maximum number of stages

    Returns:
        Configured ProgressTracker instance
    """
    return ProgressTracker(max_stages)
