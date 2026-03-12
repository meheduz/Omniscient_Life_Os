"""
Omniscient Agent - Configuration
Centralized settings for performance tuning
"""

# Audio Settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
OUTPUT_SAMPLE_RATE = 24000
OUTPUT_CHANNELS = 1
OUTPUT_CHUNK_SIZE = 2048

# Vision Settings
VISION_INTERVAL = 10  # seconds between captures
WEBCAM_WIDTH = 240
WEBCAM_HEIGHT = 180
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 270
JPEG_QUALITY = 60  # 0-100, lower = smaller file

# Memory Settings
MEMORY_COLLECTION_NAME = "omniscient_memory"
MEMORY_PERSIST_DIR = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OFFLINE_EMBEDDING_DIMENSIONS = 256
DEFAULT_SEARCH_RESULTS = 5

# Model Settings
LIVE_MODEL = "models/gemini-2.5-flash-native-audio-latest"

# Performance Settings
ENABLE_WEBCAM = True
ENABLE_SCREEN_CAPTURE = True
ENABLE_MICROPHONE = True
BATCH_DELAY = 0.01  # seconds to batch messages

# Terminal Security
ALLOWED_EXECUTABLES = [
    "python",
    "python3",
    "g++",
    "./a.out",
]
COMMAND_TIMEOUT = 60  # seconds
