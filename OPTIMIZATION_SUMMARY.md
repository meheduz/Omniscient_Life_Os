# Optimization Summary

This project is tuned around three practical constraints:

- lower live-stream bandwidth usage
- stable real-time audio behavior
- resilient memory behavior when network/model downloads are unavailable

## Implemented optimizations

1. Sensor payload reduction
- Lower webcam/screen frame sizes in `config.py`
- JPEG compression quality control via `JPEG_QUALITY`
- Batched realtime sending with `BATCH_DELAY`

2. Audio stream stability
- Increased output buffer size (`OUTPUT_CHUNK_SIZE`)
- Underflow-tolerant playback writes in `main.py`

3. Memory resilience
- Primary semantic embedding model: `all-MiniLM-L6-v2`
- Automatic offline fallback embeddings when remote model initialization fails
- Separate offline collection name to avoid embedding-config conflicts

4. Tool execution hardening
- `shell=False` execution path
- Persistent `cd` working directory across tool calls
- Centralized command timeout and allowlist in `config.py`

## Tuning knobs

The highest-impact controls are:

- `VISION_INTERVAL`
- `WEBCAM_WIDTH` / `WEBCAM_HEIGHT`
- `SCREEN_WIDTH` / `SCREEN_HEIGHT`
- `JPEG_QUALITY`
- `BATCH_DELAY`

All knobs are centralized in `config.py`.
