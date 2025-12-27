#!/bin/bash

# YouTube to Article Converter - Setup Script
# This script helps you get started with the YouTube to Article Converter

set -e  # Exit on error

echo "=========================================="
echo "YouTube to Article Converter - Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Navigate to project directory
cd "$(dirname "$0")/youtube_to_article"

# Check if .env exists
if [ -f ".env" ]; then
    echo ""
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file..."
    else
        echo "Creating new .env from template..."
        cp .env.example .env
        echo "✓ Created .env file"
    fi
else
    echo "Creating .env from template..."
    if [ ! -f ".env.example" ]; then
        echo "❌ Error: .env.example not found!"
        exit 1
    fi
    cp .env.example .env
    echo "✓ Created .env file"
fi

echo ""
echo "=========================================="
echo "HuggingFace API Token Setup"
echo "=========================================="
echo ""
echo "You need a HuggingFace API token to use this tool."
echo "Get your token at: https://huggingface.co/settings/tokens"
echo ""
read -p "Enter your HuggingFace API token (or press Enter to skip): " HF_TOKEN

if [ ! -z "$HF_TOKEN" ]; then
    # Update the .env file with the token
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env
    else
        # Linux
        sed -i "s/HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env
    fi
    echo "✓ HuggingFace token configured"
else
    echo "⚠️  Skipped token configuration. You'll need to edit .env manually."
fi

echo ""
echo "=========================================="
echo "Installing Python Dependencies"
echo "=========================================="
echo ""

# Check if virtual environment should be created
if [ ! -d "venv" ]; then
    read -p "Create a virtual environment? (recommended) (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo "✓ Virtual environment created"

        # Activate virtual environment
        source venv/bin/activate
        echo "✓ Virtual environment activated"
    fi
fi

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "=========================================="
echo "Checking FFmpeg Installation"
echo "=========================================="
echo ""

if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1)
    echo "✓ FFmpeg is installed: $FFMPEG_VERSION"
else
    echo "⚠️  FFmpeg not found in PATH"
    echo "The tool will attempt to auto-detect FFmpeg, but you may need to:"
    echo "  1. Install FFmpeg: https://ffmpeg.org/download.html"
    echo "  2. Add it to your PATH, or"
    echo "  3. Set FFMPEG_PATH in your .env file"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. If you haven't already, add your HuggingFace token to .env"
echo "  2. Launch the app:"
echo ""
if [ -d "venv" ]; then
    echo "     source venv/bin/activate  # Activate virtual environment"
fi
echo "     streamlit run app.py"
echo ""
echo "  3. Open your browser at http://localhost:8501"
echo ""
echo "Happy converting! 🎥 → 📝"
echo ""
