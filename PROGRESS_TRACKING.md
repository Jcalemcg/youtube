# Live Progress Tracking - Real-Time Step-by-Step Feedback

This document describes the real-time progress tracking system that provides step-by-step feedback during pipeline execution.

## Overview

The progress tracking system enables real-time monitoring of the YouTube-to-Article conversion pipeline with:

- **Real-time callbacks** for progress events
- **Step-by-step feedback** at each stage and step
- **Time tracking and estimates** (elapsed, remaining, total)
- **Error handling** with error callbacks
- **Cancellation support** for stopping long-running operations
- **Streamlit UI integration** for visual progress display

## Architecture

### Core Components

1. **`progress.py`** - Core progress tracking system
   - `ProgressEvent` - Data class representing a progress update
   - `ProgressTracker` - Main tracker with callback system
   - `ProgressLevel` - Event severity levels
   - `StageProgressContext` - Context manager for stage tracking

2. **`ui_progress.py`** - Streamlit UI integration
   - `StreamlitProgressDisplay` - UI components for progress
   - `create_progress_callback()` - Callback factory for UI updates
   - `show_real_time_progress()` - Display progress in Streamlit

3. **`pipeline.py`** - Updated pipeline with progress tracking
   - All stages emit progress events
   - Cancellation checks at key points
   - Time tracking for each stage

## Usage

### Basic Usage with Pipeline

```python
from pipeline import create_pipeline
from progress import create_progress_tracker

# Create a tracker
tracker = create_progress_tracker(max_stages=9)

# Add callbacks for progress updates
tracker.add_callback(my_progress_callback)
tracker.add_error_callback(my_error_callback)

# Create pipeline with tracker
pipeline = create_pipeline(progress_tracker=tracker)

# Execute pipeline - progress updates flow through callbacks
transcript = pipeline.stage1_transcribe("https://youtube.com/watch?v=...")
```

### Callback Functions

```python
from progress import ProgressEvent

def my_progress_callback(event: ProgressEvent) -> None:
    """Handle progress events."""
    print(f"Stage: {event.stage}")
    print(f"Step: {event.step}")
    print(f"Message: {event.message}")
    print(f"Progress: {event.progress:.1%}")
    print(f"Details: {event.details}")

def my_error_callback(event: ProgressEvent) -> None:
    """Handle error events."""
    print(f"ERROR: {event.message}")
    if event.error:
        print(f"Details: {event.error}")
```

### Streamlit Integration

```python
import streamlit as st
from pipeline import create_pipeline
from progress import create_progress_tracker
from ui_progress import show_real_time_progress, create_progress_callback

# Create tracker
tracker = create_progress_tracker()

# Create progress containers in UI
containers = show_real_time_progress(tracker)

# Add Streamlit callback
callback = create_progress_callback(containers)
tracker.add_callback(callback)

# Create and run pipeline
pipeline = create_pipeline(progress_tracker=tracker)
result = pipeline.stage1_transcribe(youtube_url)
```

## Progress Events

### Event Types

```python
from progress import ProgressLevel

# Available levels
ProgressLevel.DEBUG      # Detailed debug information
ProgressLevel.INFO       # Information messages
ProgressLevel.STEP       # Major step completion
ProgressLevel.MILESTONE  # Stage start/completion
ProgressLevel.WARNING    # Warning messages
ProgressLevel.ERROR      # Error messages
```

### Event Structure

```python
@dataclass
class ProgressEvent:
    timestamp: datetime           # When event occurred
    stage: str = ""              # Stage name
    step: str = ""               # Current step
    message: str = ""            # User-friendly message
    level: ProgressLevel = ...   # Severity level
    progress: float = 0.0        # Overall progress (0.0-1.0)
    details: Dict[str, Any] = {} # Additional metadata
    error: Optional[str] = None  # Error message if applicable
```

## Time Tracking

### Getting Time Estimates

```python
# Get comprehensive time estimates
estimates = tracker.get_time_estimate()
# Returns:
# {
#     'elapsed_seconds': 42.5,
#     'remaining_seconds': 87.3,
#     'total_seconds': 129.8,
#     'elapsed_minutes': 0.71,
#     'remaining_minutes': 1.46,
#     'total_minutes': 2.16
# }

# Get formatted time strings
tracker.format_time(129.8)  # Returns "2m 10s"
tracker.format_time(3661)   # Returns "1h 1m 1s"

# Get stage summary with timing info
summary = tracker.get_stage_summary()
# Includes: elapsed_formatted, remaining_formatted, etc.
```

### Stage Duration Tracking

```python
# After stages complete, track their durations
tracker.stage_durations
# {
#     'transcription': 15.3,
#     'content_filtering': 8.2,
#     'content_analysis': 12.5,
#     ...
# }

# Remaining time is estimated from average of completed stages
```

## Cancellation

### Requesting Cancellation

```python
# User requests cancellation
tracker.cancel()

# Check in pipeline code
if tracker.is_cancelled():
    raise RuntimeError("Pipeline execution cancelled by user")

# Or gracefully handle it
if tracker.is_cancelled():
    logger.info("Stopping pipeline execution")
    return None
```

### Cancellation in Streamlit

```python
# Add cancel button in UI
if st.button("🛑 Cancel Processing"):
    tracker.cancel()
    st.error("Pipeline execution cancelled")
    st.stop()

# Pipeline automatically checks cancellation and stops
```

## Pipeline Integration Details

### Stage Progress Tracking

Each stage in the pipeline:

1. **Starts** with `tracker.start_stage(stage_num, stage_name)`
2. **Updates** progress with `tracker.update()` for intermediate steps
3. **Reports** step completion with `tracker.step()`
4. **Completes** with `tracker.complete_stage(stage_name)`
5. **Handles errors** with `tracker.error()`

### Example Stage Implementation

```python
def stage1_transcribe(self, youtube_url: str) -> TranscriptResult:
    self.progress_tracker.start_stage(0, "transcription")

    try:
        # Check for cancellation
        if self.progress_tracker.is_cancelled():
            raise RuntimeError("Cancelled")

        # Progress updates during work
        self.progress_tracker.update(
            step="fetching_metadata",
            message="Fetching video metadata...",
            progress=0.1
        )

        result = self.transcriber.run(youtube_url)

        # Step completion
        self.progress_tracker.step(
            step="complete",
            message=f"✓ Transcription complete: {len(result.segments)} segments",
            details={"segments": len(result.segments)}
        )

        self.progress_tracker.complete_stage("transcription")
        return result

    except Exception as e:
        self.progress_tracker.error(
            step="transcription_failed",
            message="Transcription failed",
            error_msg=str(e)
        )
        raise
```

## Event History and Analysis

```python
# All events are stored for review
for event in tracker.events:
    print(f"{event.timestamp}: {event.message}")

# Get stage summary
summary = tracker.get_stage_summary()
print(f"Current stage: {summary['current_stage']}")
print(f"Total events: {summary['events_count']}")
print(f"Stage durations: {summary['stage_durations']}")
```

## Examples

### Example 1: Basic Progress Tracking

```python
tracker = ProgressTracker(max_stages=5)

def print_progress(event: ProgressEvent) -> None:
    print(f"[{event.level.upper()}] {event.step}: {event.message}")

tracker.add_callback(print_progress)

# Run stages
tracker.start_stage(0, "stage_1")
tracker.update("step_1", "Processing...", progress=0.5)
tracker.complete_stage("stage_1")
```

### Example 2: Time Tracking

```python
tracker = ProgressTracker(max_stages=3)

for i in range(3):
    tracker.start_stage(i, f"stage_{i+1}")
    time.sleep(1)  # Simulate work

    estimates = tracker.get_time_estimate()
    print(f"Elapsed: {tracker.format_time(estimates['elapsed_seconds'])}")
    print(f"Remaining: {tracker.format_time(estimates['remaining_seconds'])}")

    tracker.complete_stage(f"stage_{i+1}")
```

### Example 3: Error Handling

```python
tracker = ProgressTracker()

def error_handler(event: ProgressEvent) -> None:
    if event.error:
        print(f"ERROR: {event.message}")
        print(f"Details: {event.error}")

tracker.add_error_callback(error_handler)

try:
    tracker.start_stage(0, "processing")
    # ... do work ...
except Exception as e:
    tracker.error("failed", "Processing failed", str(e))
```

## Benefits

✅ **Real-time Feedback** - Users see progress immediately during long operations
✅ **Detailed Information** - Step-by-step feedback shows exactly what's happening
✅ **Time Awareness** - Estimates help users plan around processing time
✅ **Error Visibility** - Clear error messages when problems occur
✅ **Cancellation Support** - Users can stop long-running operations
✅ **Easy Integration** - Callbacks make it flexible for different UIs
✅ **Extensible** - Easy to add custom progress handlers

## Testing

Run the test suite to see all features in action:

```bash
python test_progress_tracking.py
```

This demonstrates:
- Basic progress tracking with callbacks
- Time tracking and estimates
- Error handling
- Cancellation mechanism

## Future Enhancements

Possible improvements for future versions:

1. **WebSocket Support** - Real-time updates to web clients
2. **Progress Database** - Store progress history
3. **Parallel Stage Support** - Track multiple concurrent stages
4. **Custom Metrics** - Allow stages to report custom metrics
5. **Progress Visualization** - Charts showing progress over time
6. **Retry Logic** - Automatic retry with progress updates
