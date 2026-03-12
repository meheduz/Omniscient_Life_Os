#!/bin/bash
# Optimized startup script for Omniscient Life OS

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "🚀 Starting Omniscient Life OS Agent..."

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at $VENV_DIR"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if ! python -c "import google.genai" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r "$PROJECT_DIR/requirements.txt"
    
    # Install PyAudio on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! python -c "import pyaudio" 2>/dev/null; then
            echo "🎤 Installing PyAudio..."
            if ! brew list portaudio &>/dev/null; then
                brew install portaudio
            fi
            pip install -q pyaudio
        fi
    fi
    echo "✅ Dependencies installed"
fi

# Check for API key
if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${GOOGLE_API_KEY:-}" ] && [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "❌ API key not found"
    echo "Please create a .env file with: GEMINI_API_KEY=your_key_here"
    exit 1
fi

# Check permissions on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "⚠️  Make sure to grant Microphone and Camera permissions in System Settings"
fi

# Run the agent
echo "✅ Starting agent..."
cd "$PROJECT_DIR"
python main.py

deactivate
