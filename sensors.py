"""
Omniscient Agent - Multimodal Sensor Loop (The Subconscious)
Continuous microphone streaming + periodic webcam/screen capture.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Callable, Awaitable

try:
    import pyaudio
except ImportError:
    pyaudio = None  # type: ignore[assignment]

import cv2
import mss
import numpy as np

from config import (
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_SAMPLE_RATE,
    ENABLE_SCREEN_CAPTURE,
    ENABLE_WEBCAM,
    JPEG_QUALITY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    VISION_INTERVAL,
    WEBCAM_HEIGHT,
    WEBCAM_WIDTH,
)

# Audio config for Gemini Live (16-bit PCM, 16kHz, mono)
SAMPLE_RATE = AUDIO_SAMPLE_RATE
CHANNELS = AUDIO_CHANNELS
CHUNK_SIZE = AUDIO_CHUNK_SIZE
if pyaudio is not None:
    FORMAT = pyaudio.paInt16
else:
    FORMAT = None

def _capture_webcam() -> np.ndarray | None:
    """Capture a single frame from the default webcam."""
    if not ENABLE_WEBCAM:
        return None
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        return None
    if frame.shape[:2] != (WEBCAM_HEIGHT, WEBCAM_WIDTH):
        frame = cv2.resize(frame, (WEBCAM_WIDTH, WEBCAM_HEIGHT))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame


def _capture_screen() -> np.ndarray | None:
    """Capture the primary monitor screen."""
    if not ENABLE_SCREEN_CAPTURE:
        return None
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        img = cv2.resize(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        return img


def capture_stitched_frame() -> str | None:
    """
    Capture webcam and screen, stitch side-by-side, encode to base64 JPEG.
    Returns base64 string or None on failure.
    """
    webcam = _capture_webcam()
    screen = _capture_screen()

    if webcam is None and screen is None:
        return None
    if webcam is None:
        webcam = np.zeros((WEBCAM_HEIGHT, WEBCAM_WIDTH, 3), dtype=np.uint8)
    if screen is None:
        screen = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)

    # Resize both to the same height before stitching
    target_h = WEBCAM_HEIGHT
    if webcam.shape[0] != target_h:
        scale = target_h / webcam.shape[0]
        webcam = cv2.resize(webcam, (int(webcam.shape[1] * scale), target_h))
    if screen.shape[0] != target_h:
        scale = target_h / screen.shape[0]
        screen = cv2.resize(screen, (int(screen.shape[1] * scale), target_h))

    # Stitch side-by-side: [webcam | screen]
    stitched = np.hstack([webcam, screen])
    # Use lower JPEG quality for smaller payload
    _, buf = cv2.imencode(
        ".jpg",
        cv2.cvtColor(stitched, cv2.COLOR_RGB2BGR),
        [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY],
    )
    return base64.b64encode(buf.tobytes()).decode("utf-8")


async def stream_microphone_audio(
    send_audio_chunk: Callable[[bytes], Awaitable[None]],
) -> None:
    """
    Continuously stream microphone audio to the provided callback.
    Callback receives raw 16-bit PCM chunks at 16kHz mono.
    Uses run_in_executor so the blocking stream.read() does NOT block the asyncio event loop.
    """
    if pyaudio is None:
        raise RuntimeError(
            "PyAudio is not installed. On Windows, install a pre-built wheel. See README."
        )
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    loop = asyncio.get_running_loop()

    def _read_chunk() -> bytes:
        return stream.read(CHUNK_SIZE, exception_on_overflow=False)

    try:
        while True:
            # Run the blocking read in a thread so asyncio event loop stays free
            data = await loop.run_in_executor(None, _read_chunk)
            await send_audio_chunk(data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


async def vision_loop(
    send_frame: Callable[[str], Awaitable[None]],
    interval: float = VISION_INTERVAL,
) -> None:
    """
    Background task: capture webcam + screen every `interval` seconds,
    stitch, encode to base64, and send via callback.
    """
    while True:
        await asyncio.sleep(interval)
        frame_b64 = capture_stitched_frame()
        if frame_b64:
            await send_frame(frame_b64)
