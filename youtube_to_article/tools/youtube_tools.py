"""YouTube video processing tools using yt-dlp and youtube-transcript-api."""
import os
import re
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

from models.schemas import TranscriptSegment

logger = logging.getLogger(__name__)


class YouTubeToolsError(Exception):
    """Base exception for YouTube tools."""
    pass


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


def get_video_metadata(url: str) -> Dict[str, Any]:
    """
    Fetch video metadata using yt-dlp without downloading.

    Args:
        url: YouTube URL or video ID

    Returns:
        Dictionary with video metadata

    Raises:
        YouTubeToolsError: If metadata cannot be fetched
    """
    video_id = extract_video_id(url)
    full_url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(full_url, download=False)

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
        logger.error(f"Failed to fetch metadata for {video_id}: {e}")
        raise YouTubeToolsError(f"Failed to fetch video metadata: {e}")


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
        # Try to get transcript directly using fetch method
        api = YouTubeTranscriptApi()
        caption_data = api.fetch(video_id, languages=languages)

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


def download_audio(url: str, output_dir: str = "./temp") -> str:
    """
    Download audio from YouTube video using yt-dlp.

    Args:
        url: YouTube URL or video ID
        output_dir: Directory to save audio file

    Returns:
        Path to downloaded audio file

    Raises:
        YouTubeToolsError: If download fails
    """
    video_id = extract_video_id(url)
    full_url = f"https://www.youtube.com/watch?v={video_id}"

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Output template
    output_template = str(output_path / f"{video_id}.%(ext)s")

    # FFmpeg location
    ffmpeg_location = "C:/ffmpeg/ffmpeg-master-latest-win64-gpl/bin"

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
        'ffmpeg_location': ffmpeg_location,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading audio for video {video_id}")
            ydl.download([full_url])

        # Find the downloaded file
        audio_file = output_path / f"{video_id}.wav"

        if not audio_file.exists():
            raise YouTubeToolsError(f"Audio file not found after download: {audio_file}")

        logger.info(f"Audio downloaded: {audio_file}")
        return str(audio_file)

    except Exception as e:
        logger.error(f"Failed to download audio for {video_id}: {e}")
        raise YouTubeToolsError(f"Failed to download audio: {e}")


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
