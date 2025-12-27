# YouTube to Article Converter

Convert YouTube videos into SEO-optimized articles using AI-powered multi-agent pipeline.

## Features

- **🎤 Smart Transcription**: Automatically extracts captions or uses Whisper AI transcription
- **🔍 Content Analysis**: AI analyzes structure, identifies key topics and quotes
- **✍️ Article Generation**: Transforms transcript into polished, readable articles
- **🚀 SEO Optimization**: Generates meta tags, keywords, and social media posts
- **🎨 YouTube-Themed UI**: Beautiful web interface with familiar YouTube aesthetics
- **✅ Stage-by-Stage Approval**: Review and approve each step before proceeding

## Quick Start

### Option A: Automated Setup (Recommended)

Run the setup script for your platform:

**Linux/macOS:**
```bash
./setup.sh
```

**Windows:**
```bash
setup.bat
```

The script will:
- Create `.env` from template
- Prompt for your HuggingFace API token
- Install Python dependencies
- Check FFmpeg installation

Then skip to step 3 (Launch the Web UI) below.

### Option B: Manual Setup

### 1. Install Dependencies

```bash
cd youtube_to_article
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and add your **HuggingFace API token** (required):
```bash
HF_TOKEN=your_huggingface_api_token_here
```

The `.env` file includes configuration for:
- **HuggingFace API token** (required - get yours at https://huggingface.co/settings/tokens)
- Whisper model configuration (base model, CPU mode by default)
- AI model selections (Llama 3.3 70B for analysis/writing)
- Bot detection prevention (automatic - see Bot Detection section below)
- FFmpeg path (auto-detected, customizable if needed)

### 3. Launch the Web UI

```bash
streamlit run app.py
```

This will open your browser at `http://localhost:8501`

## How to Use

### Web Interface

1. **Enter YouTube URL**: Paste any YouTube video URL
2. **Review Transcript**: Check the extracted transcript
3. **Review Analysis**: See AI-detected topics and structure
4. **Review Article**: Read the generated article, approve or regenerate
5. **Review SEO**: Check meta tags and keywords
6. **Download**: Get your article in Markdown or JSON format

### Pipeline Architecture

```
YouTube URL
    ↓
Agent 1: Transcriber
    ├─→ Try captions (fast)
    └─→ Fallback to Whisper (accurate)
    ↓
Agent 2: Content Analyzer
    └─→ Extract topics, quotes, structure
    ↓
Agent 3: Article Writer
    └─→ Generate polished article
    ↓
Agent 4: SEO Optimizer
    └─→ Add meta tags, keywords, social posts
    ↓
Final Article Package
```

## Project Structure

```
youtube_to_article/
├── app.py                  # Streamlit web UI
├── pipeline.py             # Main pipeline orchestrator
├── config/
│   └── settings.py         # Configuration management
├── agents/
│   ├── transcriber.py      # Agent 1: Transcript extraction
│   ├── analyzer.py         # Agent 2: Content analysis
│   ├── writer.py           # Agent 3: Article generation
│   └── seo_optimizer.py    # Agent 4: SEO enhancement
├── tools/
│   ├── youtube_tools.py    # YouTube API wrappers
│   └── whisper_tools.py    # Whisper transcription
├── models/
│   └── schemas.py          # Pydantic data models
├── test_phase1.py          # Test YouTube/Whisper tools
├── requirements.txt        # Python dependencies
├── .env.example            # Environment configuration template
└── .env                    # Your environment config (create from .env.example)
```

## AI Models Used

- **Content Analysis**: `meta-llama/Llama-3.3-70B-Instruct` (Hugging Face)
- **Article Writing**: `meta-llama/Llama-3.3-70B-Instruct` (Hugging Face)
- **SEO Optimization**: `meta-llama/Llama-3.1-8B-Instruct` (Hugging Face)
- **Transcription**: `faster-whisper` (base model, CPU)

## Requirements

- Python 3.10+
- FFmpeg (auto-detected, or set `FFMPEG_PATH` in `.env`)
- Hugging Face account with API access (Pro recommended for faster inference)
- Internet connection

## Testing

Run the Phase 1 test suite to verify YouTube and Whisper tools:

```bash
python test_phase1.py
```

This tests:
- Video ID extraction
- Metadata fetching
- Caption extraction
- Audio download
- Whisper transcription

## Output Format

Each processed video creates a folder with:

```
output/{video_id}/
├── complete.json       # Full pipeline output
├── article.md          # Final article (Markdown)
├── transcript.txt      # Plain text transcript
└── seo.json           # SEO package
```

## Cost Estimates

- **Hugging Face Pro**: ~$0.02 per article (LLM API calls)
- **Bandwidth**: Minimal (audio download only)
- **Processing Time**: 2-5 minutes per 10-minute video

## Bot Detection Prevention

This tool implements several anti-bot detection measures to ensure reliable YouTube access:

- **Rotating User-Agents**: Cycles through 5 different modern browser user agents
- **Realistic Headers**: Includes Accept-Language, Sec-Fetch-* headers like real browsers
- **Request Delays**: Random 1-3 second delays between requests
- **Client Alternation**: Switches between web and Android YouTube player clients
- **Retry Strategy**: Exponential backoff for failed requests

These measures work automatically - no configuration needed. For detailed technical documentation, see `BOT_DETECTION_GUIDE.md`.

## Troubleshooting

### FFmpeg Not Found
The tool auto-detects FFmpeg on your system. If you encounter errors:
1. Install FFmpeg: https://ffmpeg.org/download.html
2. Add FFmpeg to your system PATH, OR
3. Set `FFMPEG_PATH` in your `.env` file to the FFmpeg bin directory

### Whisper Running Slow
The system uses CPU mode (int8) for compatibility. For faster transcription:
1. Videos with existing captions skip Whisper entirely
2. Whisper only runs as fallback when captions unavailable

### HuggingFace API Errors
- Check your token in `.env` file
- Verify you have HF Pro subscription
- Check rate limits (30 requests/minute configured)

## License

MIT License - Feel free to use for personal or commercial projects.

## Credits

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Transcription
- [Hugging Face](https://huggingface.co/) - AI models
- [Streamlit](https://streamlit.io/) - Web interface
