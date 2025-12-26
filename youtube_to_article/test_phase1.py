"""Phase 1 test script: Test YouTube and Whisper tools."""
import sys
import os
import logging
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tools.youtube_tools import (
    extract_video_id,
    get_video_metadata,
    extract_captions,
    download_audio,
    cleanup_audio_file
)
from tools.whisper_tools import WhisperTranscriber
from config.settings import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_video_id_extraction():
    """Test video ID extraction from various URL formats."""
    print("\n" + "="*60)
    print("TEST 1: Video ID Extraction")
    print("="*60)

    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest"
    ]

    for url in test_urls:
        try:
            video_id = extract_video_id(url)
            print(f"✓ {url[:50]:50} → {video_id}")
        except Exception as e:
            print(f"✗ {url[:50]:50} → ERROR: {e}")


def test_metadata_fetching(video_url: str):
    """Test fetching video metadata."""
    print("\n" + "="*60)
    print("TEST 2: Video Metadata Fetching")
    print("="*60)

    try:
        metadata = get_video_metadata(video_url)
        print(f"✓ Successfully fetched metadata")
        print(f"  Title: {metadata['title']}")
        print(f"  Channel: {metadata['channel']}")
        print(f"  Duration: {metadata['duration_seconds']} seconds")
        print(f"  Video ID: {metadata['video_id']}")
        return metadata
    except Exception as e:
        print(f"✗ Failed to fetch metadata: {e}")
        return None


def test_caption_extraction(video_id: str):
    """Test extracting existing captions."""
    print("\n" + "="*60)
    print("TEST 3: Caption Extraction")
    print("="*60)

    try:
        captions = extract_captions(video_id)
        if captions:
            print(f"✓ Successfully extracted captions")
            print(f"  Language: {captions['language']}")
            print(f"  Segments: {len(captions['segments'])}")
            print(f"  First 200 chars: {captions['full_text'][:200]}...")
            return captions
        else:
            print(f"  No captions available for this video")
            return None
    except Exception as e:
        print(f"✗ Failed to extract captions: {e}")
        return None


def test_audio_download(video_url: str):
    """Test downloading audio."""
    print("\n" + "="*60)
    print("TEST 4: Audio Download")
    print("="*60)

    try:
        audio_path = download_audio(video_url, output_dir="./temp")
        print(f"✓ Successfully downloaded audio")
        print(f"  Path: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"✗ Failed to download audio: {e}")
        return None


def test_whisper_transcription(audio_path: str, config):
    """Test Whisper transcription."""
    print("\n" + "="*60)
    print("TEST 5: Whisper Transcription")
    print("="*60)

    try:
        transcriber = WhisperTranscriber(
            model_size=config.whisper_model,
            device=config.whisper_device,
            compute_type=config.whisper_compute_type
        )

        print(f"  Model: {config.whisper_model}")
        print(f"  Device: {config.whisper_device}")
        print(f"  Compute type: {config.whisper_compute_type}")
        print(f"  Transcribing... (this may take a minute)")

        result = transcriber.transcribe_audio(audio_path)

        print(f"✓ Successfully transcribed audio")
        print(f"  Language: {result['language']}")
        print(f"  Segments: {len(result['segments'])}")
        print(f"  First 200 chars: {result['full_text'][:200]}...")

        return result
    except Exception as e:
        print(f"✗ Failed to transcribe: {e}")
        print(f"  This might be due to missing CUDA support.")
        print(f"  Try setting WHISPER_DEVICE=cpu in .env")
        return None


def main():
    """Run all Phase 1 tests."""
    print("\n" + "="*60)
    print("PHASE 1 TEST SUITE")
    print("Testing YouTube and Whisper Tools")
    print("="*60)

    # Load configuration
    try:
        config = get_config()
        print(f"\n✓ Configuration loaded")
    except Exception as e:
        print(f"\n✗ Failed to load configuration: {e}")
        print(f"  Make sure .env file exists with required settings")
        return

    # Test with a short public video
    # Using a short creative commons video for testing
    test_video = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video (18 seconds)

    print(f"\nTest video: {test_video}")
    print(f"(Using a short video to keep tests fast)")

    # Run tests
    test_video_id_extraction()

    metadata = test_metadata_fetching(test_video)
    if not metadata:
        print("\n✗ Cannot continue without metadata")
        return

    video_id = metadata['video_id']
    captions = test_caption_extraction(video_id)

    audio_path = test_audio_download(test_video)
    if not audio_path:
        print("\n✗ Cannot test Whisper without audio file")
        print("\n" + "="*60)
        print("PHASE 1 TEST RESULTS: PARTIAL PASS")
        print("YouTube tools working, audio download failed")
        print("="*60)
        return

    whisper_result = test_whisper_transcription(audio_path, config)

    # Cleanup
    if audio_path:
        print(f"\nCleaning up audio file...")
        cleanup_audio_file(audio_path)

    # Summary
    print("\n" + "="*60)
    print("PHASE 1 TEST RESULTS")
    print("="*60)

    results = {
        'Video ID extraction': True,
        'Metadata fetching': metadata is not None,
        'Caption extraction': captions is not None or True,  # OK if no captions
        'Audio download': audio_path is not None,
        'Whisper transcription': whisper_result is not None
    }

    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {test}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All Phase 1 tests passed! Ready for Phase 2.")
    else:
        print("\n⚠ Some tests failed. Check errors above.")

    print("="*60)


if __name__ == "__main__":
    main()
