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

### 1. Install Dependencies

```bash
cd youtube_to_article
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with your settings. It includes:
- Hugging Face API token
- Whisper model configuration (CPU mode)
- AI model selections

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
└── .env                    # Environment configuration
```

## AI Models Used

- **Content Analysis**: `meta-llama/Llama-3.3-70B-Instruct` (Hugging Face)
- **Article Writing**: `meta-llama/Llama-3.3-70B-Instruct` (Hugging Face)
- **SEO Optimization**: `meta-llama/Llama-3.1-8B-Instruct` (Hugging Face)
- **Transcription**: `faster-whisper` (base model, CPU)

## Requirements

- Python 3.10+
- FFmpeg (already installed at `C:/ffmpeg/`)
- Hugging Face Pro account (for LLM API access)
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

## Troubleshooting

### FFmpeg Not Found
FFmpeg is installed at `C:/ffmpeg/ffmpeg-master-latest-win64-gpl/bin`
If you get errors, the installation is already configured in the code.

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
