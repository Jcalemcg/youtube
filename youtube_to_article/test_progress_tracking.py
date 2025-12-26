"""Example demonstrating real-time progress tracking with callbacks."""

import time
from progress import ProgressTracker, ProgressEvent, ProgressLevel


def simple_progress_callback(event: ProgressEvent) -> None:
    """Simple callback that prints progress events."""
    print(str(event))


def detailed_callback(event: ProgressEvent) -> None:
    """Detailed callback showing full event information."""
    print(f"\n{'=' * 60}")
    print(f"PROGRESS EVENT")
    print(f"{'=' * 60}")
    print(f"Timestamp: {event.timestamp.strftime('%H:%M:%S')}")
    print(f"Stage: {event.stage}")
    print(f"Step: {event.step}")
    print(f"Message: {event.message}")
    print(f"Level: {event.level.value}")
    print(f"Progress: {event.progress:.1%}")
    if event.details:
        print(f"Details:")
        for key, value in event.details.items():
            print(f"  {key}: {value}")
    if event.error:
        print(f"Error: {event.error}")
    print(f"{'=' * 60}\n")


def example_with_callbacks():
    """Example showing progress tracking with callbacks."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Progress Tracking with Callbacks")
    print("=" * 60 + "\n")

    # Create tracker
    tracker = ProgressTracker(max_stages=9)

    # Add callbacks
    tracker.add_callback(simple_progress_callback)

    # Simulate pipeline execution
    stages = [
        ("transcription", 2.0),
        ("content_filtering", 1.5),
        ("content_analysis", 3.0),
        ("article_writing", 4.0),
        ("seo_optimization", 2.0),
        ("quality_assessment", 1.5),
    ]

    for i, (stage_name, duration) in enumerate(stages):
        print(f"\n--- Starting {stage_name.replace('_', ' ').title()} ---")
        tracker.start_stage(i, stage_name)

        # Simulate work with progress updates
        steps_count = 3
        for step in range(steps_count):
            tracker.update(
                step=f"step_{step + 1}",
                message=f"Processing {stage_name}: step {step + 1}/{steps_count}",
                progress=(step + 1) / steps_count
            )
            time.sleep(duration / steps_count)  # Simulate work

        tracker.step(
            step="complete",
            message=f"Completed {stage_name}",
            details={"duration_seconds": duration}
        )
        tracker.complete_stage(stage_name)

    # Show final summary
    summary = tracker.get_stage_summary()
    print(f"\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Total elapsed: {summary['total_elapsed_formatted']}")
    print(f"Estimated remaining: {summary['estimated_remaining_formatted']}")
    print(f"Estimated total: {summary['estimated_total_formatted']}")
    print(f"Total events: {summary['events_count']}")
    print(f"{'=' * 60}\n")


def example_with_time_tracking():
    """Example showing time tracking and estimates."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Time Tracking and Estimates")
    print("=" * 60 + "\n")

    tracker = ProgressTracker(max_stages=5)

    # Simulate stages with varying durations
    stage_durations = [
        ("stage_1", 1.0),
        ("stage_2", 1.5),
        ("stage_3", 1.2),
    ]

    for i, (stage_name, duration) in enumerate(stage_durations):
        tracker.start_stage(i, stage_name)
        time.sleep(duration)

        # Show time estimates after each stage
        estimates = tracker.get_time_estimate()
        print(f"\n{stage_name.upper()} - Time Estimates:")
        print(f"  Elapsed: {tracker.format_time(estimates['elapsed_seconds'])}")
        print(f"  Estimated remaining: {tracker.format_time(estimates['remaining_seconds'])}")
        print(f"  Estimated total: {tracker.format_time(estimates['total_seconds'])}")

        tracker.complete_stage(stage_name)

    # Show final time breakdown
    print(f"\n{'=' * 60}")
    print("FINAL TIME BREAKDOWN")
    print(f"{'=' * 60}")
    summary = tracker.get_stage_summary()
    for stage, duration in summary['stage_durations'].items():
        print(f"{stage}: {tracker.format_time(duration)}")
    print(f"Total elapsed: {summary['total_elapsed_formatted']}")
    print(f"{'=' * 60}\n")


def example_with_error_handling():
    """Example showing error handling."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Error Handling")
    print("=" * 60 + "\n")

    tracker = ProgressTracker(max_stages=5)

    # Add error callback
    def error_callback(event: ProgressEvent) -> None:
        print(f"[ERROR CALLBACK] {event.message}")
        if event.error:
            print(f"[ERROR DETAILS] {event.error}")

    tracker.add_error_callback(error_callback)

    # Simulate stages with an error
    try:
        tracker.start_stage(0, "stage_with_error")
        tracker.update(
            step="processing",
            message="Processing data...",
            progress=0.5
        )

        # Simulate error
        raise ValueError("Simulated processing error")

    except ValueError as e:
        tracker.error(
            step="processing_failed",
            message="Error during processing",
            error_msg=str(e)
        )

    print("\nError handling complete.\n")


def example_with_cancellation():
    """Example showing cancellation mechanism."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Cancellation Mechanism")
    print("=" * 60 + "\n")

    tracker = ProgressTracker(max_stages=5)

    def progress_callback(event: ProgressEvent) -> None:
        print(f"[PROGRESS] {event.step}: {event.message}")

    tracker.add_callback(progress_callback)

    # Simulate stages with cancellation
    tracker.start_stage(0, "stage_1")
    print("Stage 1: Processing...")
    time.sleep(0.5)

    # Request cancellation
    print("\n[USER] Requesting cancellation...")
    tracker.cancel()

    # Check if cancelled
    if tracker.is_cancelled():
        print("[SYSTEM] Cancellation detected, stopping pipeline execution")
        tracker.error(
            step="cancelled",
            message="Pipeline execution cancelled by user",
            error_msg="User requested cancellation"
        )
    else:
        print("[SYSTEM] Continuing with stage execution...")

    print("\nCancellation example complete.\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PROGRESS TRACKING EXAMPLES")
    print("=" * 60)

    # Run examples
    example_with_callbacks()
    example_with_time_tracking()
    example_with_error_handling()
    example_with_cancellation()

    print("\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
