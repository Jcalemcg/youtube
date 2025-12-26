"""Quick test script to verify YouTube bot detection fixes."""
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'youtube_to_article'))

from tools.youtube_tools import get_video_metadata, extract_video_id

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_video(url):
    """Test fetching metadata from a video."""
    try:
        logger.info(f"Testing video: {url}")

        # Extract video ID
        video_id = extract_video_id(url)
        logger.info(f"Video ID: {video_id}")

        # Get metadata
        metadata = get_video_metadata(url)

        logger.info("✅ Success! Metadata retrieved:")
        logger.info(f"  Title: {metadata['title']}")
        logger.info(f"  Channel: {metadata['channel']}")
        logger.info(f"  Duration: {metadata['duration_seconds']}s")
        logger.info(f"  Views: {metadata.get('view_count', 'N/A')}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    # Test with the problematic video ID or a sample video
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    success = test_video(test_url)
    sys.exit(0 if success else 1)
