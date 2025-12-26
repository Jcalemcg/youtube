"""Test the content filtering system."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from youtube_to_article.agents.content_filter import ContentFilterAgent
from youtube_to_article.models.schemas import TranscriptResult, TranscriptSegment

def test_content_filter():
    """Test the content filter agent."""
    print("=" * 60)
    print("Testing Content Filter Agent")
    print("=" * 60 + "\n")

    # Initialize filter
    filter_agent = ContentFilterAgent()
    print("✓ Content Filter Agent initialized\n")

    # Test 1: Clean content
    print("Test 1: Clean Content")
    print("-" * 40)
    clean_transcript = TranscriptResult(
        video_id="test1",
        title="Python Tutorial",
        channel="Tech Channel",
        duration_seconds=600,
        transcript="In this tutorial, we'll learn about Python programming. Python is a powerful language for web development and data science.",
        segments=[
            TranscriptSegment(start=0, end=30, text="In this tutorial, we'll learn about Python programming."),
            TranscriptSegment(start=30, end=60, text="Python is a powerful language for web development and data science.")
        ],
        source="captions",
        language="en"
    )

    result1 = filter_agent.filter_transcript(clean_transcript)
    print(f"Compliance Status: {result1.overall_compliance}")
    print(f"Promotional Score: {result1.promotional_score:.1%}")
    print(f"Flags Detected: {len(result1.flags)}")
    print(f"Summary: {result1.summary}\n")

    # Test 2: Promotional content
    print("Test 2: Promotional Content")
    print("-" * 40)
    promo_transcript = TranscriptResult(
        video_id="test2",
        title="Limited Time Offer!",
        channel="Sales Channel",
        duration_seconds=600,
        transcript="Buy now! Don't miss this exclusive offer! Use promo code SAVE20 for 20% off. Act now before it's gone. Get your discount today!",
        segments=[
            TranscriptSegment(start=0, end=30, text="Buy now! Don't miss this exclusive offer!"),
            TranscriptSegment(start=30, end=60, text="Use promo code SAVE20 for 20% off."),
            TranscriptSegment(start=60, end=90, text="Act now before it's gone. Get your discount today!")
        ],
        source="captions",
        language="en"
    )

    result2 = filter_agent.filter_transcript(promo_transcript)
    print(f"Compliance Status: {result2.overall_compliance}")
    print(f"Promotional Score: {result2.promotional_score:.1%}")
    print(f"Sponsor Mentions: {result2.sponsor_mentions}")
    print(f"Flags Detected: {len(result2.flags)}")
    print(f"Summary: {result2.summary}\n")

    # Test 3: Content with potential policy issues
    print("Test 3: Sponsored Content")
    print("-" * 40)
    sponsored_transcript = TranscriptResult(
        video_id="test3",
        title="Tech Review",
        channel="Review Channel",
        duration_seconds=600,
        transcript="This video is sponsored by TechBrand. We appreciate their support. Now let's look at their new product. TechBrand has really outdone themselves with this innovation.",
        segments=[
            TranscriptSegment(start=0, end=30, text="This video is sponsored by TechBrand. We appreciate their support."),
            TranscriptSegment(start=30, end=60, text="Now let's look at their new product."),
            TranscriptSegment(start=60, end=90, text="TechBrand has really outdone themselves with this innovation.")
        ],
        source="captions",
        language="en"
    )

    result3 = filter_agent.filter_transcript(sponsored_transcript)
    print(f"Compliance Status: {result3.overall_compliance}")
    print(f"Is Sponsor Content: {result3.is_sponsor_content}")
    print(f"Sponsor Mentions: {result3.sponsor_mentions}")
    print(f"Promotional Score: {result3.promotional_score:.1%}")
    print(f"Flags Detected: {len(result3.flags)}")
    for flag in result3.flags:
        print(f"  - {flag.category}: {flag.message}")
    print(f"Summary: {result3.summary}\n")

    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_content_filter()
