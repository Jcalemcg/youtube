"""YouTube video processing tools using yt-dlp and youtube-transcript-api."""
import os
import re
import time
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import random
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

from models.schemas import TranscriptSegment

logger = logging.getLogger(__name__)

# User-Agent rotation pool - mimics real browser behavior (updated to latest versions)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
]

# Request headers that mimic real browser behavior
COMMON_HEADERS = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

# Minimum and maximum delays between requests (in seconds)
MIN_REQUEST_DELAY = 1
MAX_REQUEST_DELAY = 3


class YouTubeToolsError(Exception):
    """Base exception for YouTube tools."""
    pass


def get_headers() -> Dict[str, str]:
    """
    Get randomized headers that mimic real browser behavior.

    Returns:
        Dictionary of HTTP headers
    """
    headers = COMMON_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    return headers


def apply_request_delay():
    """
    Apply a random delay between requests to avoid bot detection.
    Delays between MIN_REQUEST_DELAY and MAX_REQUEST_DELAY seconds.
    """
    delay = random.uniform(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY)
    time.sleep(delay)
    logger.debug(f"Applied request delay: {delay:.2f}s")


def extract_video_id(url: str) -> str:
    """
    Extract video ID from YouTube URL.

    Supports formats:
    - https://youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/watch?v=VIDEO_ID&other=params

    Args:
        url: YouTube URL or video ID

    Returns:
        Video ID string

    Raises:
        YouTubeToolsError: If video ID cannot be extracted
    """
    # If it's already just an ID, return it
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    # Extract from URL
    patterns = [
        r'(?:v=|/)([a-zA-Z0-9_-]{11}).*',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'embed/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise YouTubeToolsError(f"Could not extract video ID from: {url}")


def get_video_metadata(url: str, use_cookies: bool = True) -> Dict[str, Any]:
    """
    Fetch video metadata using yt-dlp without downloading.

    Args:
        url: YouTube URL or video ID
        use_cookies: Whether to try extracting cookies from browser (default: True)

    Returns:
        Dictionary with video metadata

    Raises:
        YouTubeToolsError: If metadata cannot be fetched
    """
    video_id = extract_video_id(url)
    full_url = f"https://www.youtube.com/watch?v={video_id}"

    # Try Firefox first (more reliable than Chrome on Windows)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'http_headers': get_headers(),
        'socket_timeout': 30,
    }

    # Try with Firefox cookies if available
    if use_cookies:
        try:
            ydl_opts['cookiesfrombrowser'] = ('firefox', None)
            logger.info("Using Firefox cookies for authentication")
        except Exception as e:
            logger.debug(f"Firefox cookies unavailable: {e}")
            # Continue without cookies

    try:
        apply_request_delay()  # Add delay before request

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(full_url, download=False)

            logger.info("✅ Successfully fetched metadata")
            return {
                'video_id': video_id,
                'url': full_url,
                'title': info.get('title', 'Unknown'),
                'channel': info.get('uploader', 'Unknown'),
                'duration_seconds': info.get('duration', 0),
                'thumbnail_url': info.get('thumbnail'),
                'upload_date': info.get('upload_date'),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
            }
    except Exception as e:
        logger.warning(f"Full metadata extraction failed: {e}")
        # Try fallback method
        return _get_metadata_fallback(video_id)


def _get_metadata_fallback(video_id: str) -> Dict[str, Any]:
    """
    Fallback metadata extraction using BeautifulSoup (no JavaScript required).

    Args:
        video_id: YouTube video ID

    Returns:
        Dictionary with basic video metadata

    Raises:
        YouTubeToolsError: If fallback also fails
    """
    import requests
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("BeautifulSoup4 not installed. Install with: pip install beautifulsoup4")
        raise YouTubeToolsError("Metadata fallback requires beautifulsoup4")

    try:
        logger.info("Trying fallback metadata extraction...")
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.9',
        }

        apply_request_delay()
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract from meta tags
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else 'Unknown'

        duration_tag = soup.find('meta', itemprop='duration')
        duration_str = duration_tag['content'] if duration_tag else 'PT0S'

        # Convert PT format to seconds
        duration_seconds = 0
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            duration_seconds = hours * 3600 + minutes * 60 + seconds

        logger.info("✅ Fallback metadata extraction successful")
        return {
            'video_id': video_id,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'title': title,
            'channel': 'Unknown',
            'duration_seconds': duration_seconds,
            'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            'upload_date': None,
            'description': '',
            'view_count': 0,
            'like_count': 0,
        }
    except Exception as e:
        logger.error(f"Metadata fallback failed: {e}")
        raise YouTubeToolsError(
            f"Failed to fetch metadata using both primary and fallback methods. "
            f"YouTube may be blocking requests. Try again later. Error: {e}"
        )


def extract_captions(video_id: str, languages: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Pull existing YouTube captions using youtube-transcript-api.

    Args:
        video_id: YouTube video ID
        languages: Preferred languages (default: ['en'])

    Returns:
        Dictionary with transcript data or None if unavailable
        {
            'segments': List[TranscriptSegment],
            'full_text': str,
            'language': str,
            'source': 'captions'
        }

    Raises:
        YouTubeToolsError: If there's an error (other than transcript unavailable)
    """
    if languages is None:
        languages = ['en']

    try:
        apply_request_delay()  # Add delay before request

        # Create custom headers for transcript API
        headers = get_headers()

        # Try to get transcript directly using fetch method
        api = YouTubeTranscriptApi()
        caption_data = api.fetch(video_id, languages=languages, http_client=None)

        # Convert to our format
        segments = []
        full_text_parts = []

        for entry in caption_data:
            segment = TranscriptSegment(
                start=entry['start'],
                end=entry['start'] + entry['duration'],
                text=entry['text'],
                confidence=None  # Captions don't provide confidence scores
            )
            segments.append(segment)
            full_text_parts.append(entry['text'])

        apply_request_delay()  # Add delay after successful request

        return {
            'segments': segments,
            'full_text': ' '.join(full_text_parts),
            'language': languages[0],  # Return requested language
            'source': 'captions'
        }

    except TranscriptsDisabled:
        logger.info(f"Captions disabled for video {video_id}")
        return None
    except NoTranscriptFound:
        logger.info(f"No captions available for video {video_id}")
        return None
    except VideoUnavailable:
        raise YouTubeToolsError(f"Video {video_id} is unavailable")
    except Exception as e:
        logger.warning(f"Error extracting captions for {video_id}: {e}")
        return None


def download_audio(url: str, output_dir: str = "./temp", use_cookies: bool = True, max_retries: int = 3) -> str:
    """
    Download audio from YouTube video using yt-dlp with retry logic.

    Args:
        url: YouTube URL or video ID
        output_dir: Directory to save audio file
        use_cookies: Whether to try extracting cookies from browser (default: True)
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        Path to downloaded audio file

    Raises:
        YouTubeToolsError: If download fails after all retries
    """
    video_id = extract_video_id(url)
    full_url = f"https://www.youtube.com/watch?v={video_id}"

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Output template
    output_template = str(output_path / f"{video_id}.%(ext)s")

    # Get FFmpeg location (cross-platform compatible)
    ffmpeg_location = os.environ.get('FFMPEG_PATH', None)

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Download attempt {attempt + 1}/{max_retries}")

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'http_headers': get_headers(),
                'socket_timeout': 30,
                'retries': 5,
                'fragment_retries': 5,
            }

            # Try Firefox cookies on first attempt
            if use_cookies and attempt == 0:
                try:
                    ydl_opts['cookiesfrombrowser'] = ('firefox', None)
                    logger.info("Using Firefox cookies for authentication")
                except Exception as e:
                    logger.debug(f"Firefox cookies unavailable: {e}")

            # Add FFmpeg location only if explicitly set
            if ffmpeg_location:
                ydl_opts['ffmpeg_location'] = ffmpeg_location

            # Add delay on retries
            if attempt > 0:
                delay = 5 * attempt  # 5s, 10s, 15s...
                logger.info(f"Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                apply_request_delay()

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([full_url])

            # Find the downloaded file
            audio_file = output_path / f"{video_id}.wav"

            if not audio_file.exists():
                raise YouTubeToolsError(f"Audio file not found after download: {audio_file}")

            logger.info(f"✅ Audio downloaded successfully")
            return str(audio_file)

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)[:150]}")

            if attempt == max_retries - 1:
                # Final attempt failed
                logger.error(f"❌ Failed to download audio after {max_retries} attempts")
                raise YouTubeToolsError(
                    f"Failed to download audio after {max_retries} attempts. "
                    f"YouTube may have updated bot detection. "
                    f"Try manually uploading audio or waiting 24 hours. "
                    f"Error: {last_error}"
                )

    # Should not reach here, but just in case
    raise YouTubeToolsError(f"Audio download failed: {last_error}")


def cleanup_audio_file(file_path: str) -> None:
    """
    Delete downloaded audio file to free space.

    Args:
        file_path: Path to audio file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up audio file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup audio file {file_path}: {e}")
