# Omniscient Context-Aware Agent

A pure Python backend daemon for the Gemini Live Agent Challenge. It acts as a proactive Life OS and research partner with:

- Live voice interaction
- Webcam and screen sensing
- Long-term memory with vector search
- Autonomous tool use (terminal + memory)

## Architecture

| Module | Role |
|--------|------|
| `main.py` | Daemon entry point; Gemini Live session, sensor orchestration, tool dispatch |
| `memory.py` | ChromaDB long-term memory (The Hippocampus) |
| `sensors.py` | Multimodal sensor loop: microphone stream + webcam/screen capture |
| `tools.py` | Function calling: `execute_terminal`, `save_memory`, `search_memory` |

## Tech Stack

- Python 3.10+
- `google-genai` (Gemini Live API)
- `websockets`, `asyncio`
- `pyaudio` (microphone/speaker)
- `opencv-python` (webcam)
- `mss` (screen capture)
- `chromadb`, `sentence-transformers` (long-term memory)

## Quick Start (Windows)

### 1. Open project folder

```powershell
cd "path\to\Omniscient Life OS"
```

### 2. Create and activate virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure API key

Create a `.env` file in the project root with:

```env
GEMINI_API_KEY=your_api_key_here
```

### 5. Run the agent

```powershell
python main.py
```

## PyAudio on Windows

On Windows, `pip install pyaudio` may fail because PortAudio build tools are missing.

Recommended installation for Python 3.12+:

```powershell
pip install --extra-index-url https://pypi.anaconda.org/scientific-python-nightly-wheels/simple PyAudio
```

Alternative wheel sources:

1. https://github.com/intxcc/pyaudio_portaudio/releases
2. https://github.com/davidacm/pyaudio_portaudioBuilds/releases

Install a downloaded wheel like:

```powershell
pip install path\to\PyAudio-0.2.14-cp312-cp312-win_amd64.whl
```

Note: `pipwin` is currently unreliable on Python 3.11+ due to `js2py` compatibility issues.

## Start, Stop, and Interaction Guide

For a complete operational guide, see:

- `run&stop.md`

It includes:

- how to start the agent
- how to stop normal and stuck processes
- how to interact effectively (voice + sensor context)

## Current Live Model

The project is configured to use:

- `models/gemini-2.5-flash-native-audio-latest`

If you get a model `NOT_FOUND` error, run a model list check and update the model constant in `main.py`.

## Autonomous Tools

- `execute_terminal(command)`: run allowed terminal commands
- `save_memory(fact)`: store facts in ChromaDB
- `search_memory(query)`: retrieve relevant prior context

## Persona

The agent is designed as a proactive Life OS and physics/engineering research partner. It can:

- observe room + screen context continuously
- use memory to provide personalized guidance
- interrupt based on known constraints (for example sleep schedule)
- debate technical ideas and run code/tools when needed
