"""Streamlit UI components for real-time progress tracking."""

import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime
import time

from progress import ProgressEvent, ProgressLevel, ProgressTracker


class StreamlitProgressDisplay:
    """Manages Streamlit UI components for progress display."""

    def __init__(self):
        """Initialize progress display."""
        self.status_container = None
        self.progress_bar = None
        self.details_container = None
        self.timeline_container = None
        self.current_events: List[ProgressEvent] = []

        # Initialize session state for progress display
        if 'progress_events' not in st.session_state:
            st.session_state.progress_events = []
        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = ""

    def create_progress_containers(self) -> Dict[str, Any]:
        """
        Create Streamlit containers for progress display.

        Returns:
            Dictionary with container references
        """
        containers = {
            'status': st.empty(),
            'progress': st.empty(),
            'details': st.empty(),
            'timeline': st.empty()
        }
        return containers

    def update_progress_display(
        self,
        event: ProgressEvent,
        containers: Dict[str, Any]
    ) -> None:
        """
        Update Streamlit UI with progress event.

        Args:
            event: Progress event to display
            containers: Dictionary with Streamlit containers
        """
        # Add to session state
        st.session_state.progress_events.append(event)

        # Update status message
        self._update_status(event, containers['status'])

        # Update progress bar
        self._update_progress_bar(event, containers['progress'])

        # Update details section
        self._update_details(event, containers['details'])

    def _update_status(self, event: ProgressEvent, container) -> None:
        """Update status message container."""
        with container:
            if event.error or event.level == ProgressLevel.ERROR:
                st.error(f"❌ {event.message}")
                if event.error:
                    st.code(event.error, language="text")

            elif event.level == ProgressLevel.MILESTONE:
                st.info(f"🎯 {event.message}")

            elif event.level == ProgressLevel.STEP:
                st.success(f"✓ {event.message}")

            elif event.level == ProgressLevel.WARNING:
                st.warning(f"⚠️ {event.message}")

            else:  # INFO or DEBUG
                st.info(f"ℹ️ {event.message}")

    def _update_progress_bar(self, event: ProgressEvent, container) -> None:
        """Update progress bar container."""
        with container:
            if event.progress > 0:
                st.progress(
                    min(event.progress, 1.0),
                    text=f"Progress: {event.progress:.0%}"
                )

    def _update_details(self, event: ProgressEvent, container) -> None:
        """Update details container."""
        if not event.details:
            return

        with container:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Stage", event.stage)
            with col2:
                st.metric("Step", event.step or "—")

            # Show additional details
            if event.details:
                st.caption("📊 Details")
                for key, value in event.details.items():
                    st.text(f"{key}: {value}")

    def show_progress_timeline(
        self,
        events: List[ProgressEvent],
        container
    ) -> None:
        """
        Display a timeline of progress events.

        Args:
            events: List of progress events
            container: Streamlit container
        """
        with container:
            st.subheader("📅 Progress Timeline")

            # Group events by stage
            stages: Dict[str, List[ProgressEvent]] = {}
            for event in events:
                if event.stage not in stages:
                    stages[event.stage] = []
                stages[event.stage].append(event)

            # Display each stage
            for stage, stage_events in stages.items():
                with st.expander(f"**{stage}**", expanded=False):
                    for event in stage_events:
                        # Format timestamp
                        time_str = event.timestamp.strftime("%H:%M:%S")

                        # Build message with level indicator
                        level_emoji = {
                            ProgressLevel.DEBUG: "🔍",
                            ProgressLevel.INFO: "ℹ️",
                            ProgressLevel.STEP: "✓",
                            ProgressLevel.MILESTONE: "🎯",
                            ProgressLevel.WARNING: "⚠️",
                            ProgressLevel.ERROR: "❌"
                        }.get(event.level, "•")

                        st.text(
                            f"{time_str} {level_emoji} {event.step}: {event.message}"
                        )

                        if event.error:
                            st.code(event.error, language="text")

    def show_stage_progress(
        self,
        current_stage: int,
        total_stages: int,
        stage_names: List[str]
    ) -> None:
        """
        Display stage progress with visual indicators.

        Args:
            current_stage: Current stage number (0-based)
            total_stages: Total number of stages
            stage_names: List of stage names
        """
        # Create columns for each stage
        cols = st.columns(total_stages)

        for i, (col, stage_name) in enumerate(zip(cols, stage_names)):
            with col:
                if i < current_stage:
                    # Completed stage
                    st.success(f"✓\n{stage_name}")
                elif i == current_stage:
                    # Current stage
                    st.info(f"→\n{stage_name}")
                else:
                    # Pending stage
                    st.text(f"◯\n{stage_name}")

    def show_detailed_progress(
        self,
        tracker: ProgressTracker,
        container
    ) -> None:
        """
        Show detailed progress information.

        Args:
            tracker: ProgressTracker instance
            container: Streamlit container
        """
        with container:
            summary = tracker.get_stage_summary()

            # Create metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Current Stage", summary['current_stage'])

            with col2:
                st.metric("Current Step", summary['current_step'] or "—")

            with col3:
                elapsed = summary['total_elapsed']
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                st.metric("Elapsed Time", f"{minutes}m {seconds}s")

            with col4:
                st.metric("Events", summary['events_count'])


def create_progress_callback(containers: Dict[str, Any]) -> callable:
    """
    Create a callback function for progress events.

    Args:
        containers: Dictionary with Streamlit containers

    Returns:
        Callback function for use with ProgressTracker
    """
    display = StreamlitProgressDisplay()

    def callback(event: ProgressEvent) -> None:
        """Handle progress event."""
        display.update_progress_display(event, containers)

    return callback


def create_error_callback(containers: Dict[str, Any]) -> callable:
    """
    Create a callback function for error events.

    Args:
        containers: Dictionary with Streamlit containers

    Returns:
        Callback function for error events
    """
    display = StreamlitProgressDisplay()

    def callback(event: ProgressEvent) -> None:
        """Handle error event."""
        display.update_progress_display(event, containers)

    return callback


def show_real_time_progress(
    tracker: ProgressTracker,
    stage_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Show real-time progress display in Streamlit.

    Args:
        tracker: ProgressTracker instance
        stage_names: List of stage names for progress indicator

    Returns:
        Dictionary with containers for further updates
    """
    # Create default stage names if not provided
    if stage_names is None:
        stage_names = [
            "Input",
            "Transcribe",
            "Filter",
            "Analyze",
            "Theme",
            "Write",
            "SEO",
            "QA",
            "Complete"
        ]

    # Create display instance
    display = StreamlitProgressDisplay()

    # Create containers
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Progress")
        containers = display.create_progress_containers()
    with col2:
        st.subheader("Stage Progress")
        display.show_stage_progress(
            tracker.current_stage,
            len(stage_names),
            stage_names
        )

    return containers


class ProgressContextManager:
    """Context manager for progress tracking in Streamlit."""

    def __init__(
        self,
        tracker: ProgressTracker,
        stage_num: int,
        stage_name: str,
        containers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize context manager.

        Args:
            tracker: ProgressTracker instance
            stage_num: Stage number (0-based)
            stage_name: Stage name
            containers: Streamlit containers for updates
        """
        self.tracker = tracker
        self.stage_num = stage_num
        self.stage_name = stage_name
        self.containers = containers

    def __enter__(self):
        """Enter context and setup progress tracking."""
        self.tracker.start_stage(self.stage_num, self.stage_name)

        # Setup callbacks if containers provided
        if self.containers:
            display = StreamlitProgressDisplay()
            self.tracker.add_callback(
                create_progress_callback(self.containers)
            )
            self.tracker.add_error_callback(
                create_error_callback(self.containers)
            )

        return self.tracker

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and finalize progress tracking."""
        if exc_type is not None:
            self.tracker.error(
                step="stage_error",
                message=f"Error in {self.stage_name}",
                error_msg=str(exc_val)
            )
        else:
            self.tracker.complete_stage(self.stage_name)

        return False
