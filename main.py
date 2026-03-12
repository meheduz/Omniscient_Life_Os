"""
Omniscient Context-Aware Agent - Main Daemon
Gemini Live Agent Challenge: Proactive Life OS, research partner, terminal controller.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import os
import sys
from typing import Any

import io
from dotenv import load_dotenv
load_dotenv()

from config import (
    AUDIO_SAMPLE_RATE,
    BATCH_DELAY,
    ENABLE_MICROPHONE,
    ENABLE_SCREEN_CAPTURE,
    ENABLE_WEBCAM,
    LIVE_MODEL,
    OUTPUT_CHANNELS,
    OUTPUT_CHUNK_SIZE,
    OUTPUT_SAMPLE_RATE,
)


def _force_utf8_streams() -> None:
    """Force UTF-8 output streams where supported (mostly for Windows terminals)."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "buffer"):
            wrapped = io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
            setattr(sys, stream_name, wrapped)


_force_utf8_streams()
print("Starting Omniscient Life OS Agent...", flush=True)


try:
    import pyaudio
except ImportError:
    pyaudio = None  # type: ignore[assignment]

from google import genai
from google.genai import types

from memory import init_memory
from sensors import stream_microphone_audio, vision_loop
from tools import execute_terminal, save_memory, search_memory, get_gemini_tools

if pyaudio is not None:
    OUTPUT_FORMAT = pyaudio.paInt16
else:
    OUTPUT_FORMAT = None


SYSTEM_INSTRUCTION = """You are a proactive, highly intelligent Life OS and physics/engineering research partner.

You continuously see my physical room (via webcam) and my digital screen (via screen capture). You have access to my terminal and my long-term memory database.

Be proactive:
- If you see me eating, check my memory for diet goals and comment if relevant.
- If you see me coding past my optimized sleep schedule v1.1, verbally interrupt to tell me to sleep.
- If we are discussing complex physics or algorithms, actively debate the math and autonomously use your terminal tool to generate and execute Python scripts to plot the graphs we discuss.

Do NOT wait for me to ask you to use a tool. If a terminal action or memory retrieval is logically required, execute it autonomously. You have full permission to call execute_terminal, save_memory, and search_memory whenever it makes sense."""


def _play_audio_chunk(stream, data: bytes) -> None:
    """Play a chunk of PCM audio to the default output device."""
    if not data:
        return
    try:
        stream.write(data, exception_on_underflow=False)
    except Exception:
        pass


async def _handle_tool_call(
    session: Any,
    function_call: Any,
    memory_collection: Any,
) -> None:
    """Execute a tool call and send the response back to the session."""
    name = function_call.name
    fc_id = getattr(function_call, "id", None)
    args = dict(function_call.args) if function_call.args else {}

    result: Any = None
    if name == "execute_terminal":
        result = execute_terminal(args.get("command", ""))
    elif name == "save_memory":
        doc_id = save_memory(args.get("fact", ""), memory_collection)
        result = {"saved": True, "id": doc_id}
    elif name == "search_memory":
        hits = search_memory(
            args.get("query", ""),
            n_results=args.get("n_results", 5),
            collection=memory_collection,
        )
        result = [{"document": h["document"], "metadata": h["metadata"]} for h in hits]
    else:
        result = {"error": f"Unknown tool: {name}"}

    fr_kw = {"name": name, "response": {"result": result}}
    if fc_id is not None:
        fr_kw["id"] = fc_id
    await session.send_tool_response(
        function_responses=[types.FunctionResponse(**fr_kw)],
    )


async def run_agent() -> None:
    """Main agent loop: connect to Gemini Live, stream sensors, handle tools."""
    if pyaudio is None:
        print(
            "PyAudio is not installed. Mic/speaker will not work.\n"
            "On Windows, pip often fails to build PyAudio. Install a pre-built wheel:\n"
            "  1. Open https://github.com/intxcc/pyaudio_portaudio/releases\n"
            "  2. Download the .whl for your Python (e.g. cp312 = 3.12) and win_amd64\n"
            "  3. Run: pip install path\\to\\PyAudio-0.2.14-cp312-cp312-win_amd64.whl\n"
            "Or try: pip install pipwin && pipwin install pyaudio"
        )
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    memory_collection = init_memory()
    print(f"Connecting to Gemini Live with model: {LIVE_MODEL}", flush=True)
    print("Initializing audio and sensor streams...", flush=True)


    # Live API config (model passed to connect())
    # Note: some fields (like proactivity) are not yet supported by all backends,
    # so we keep the config minimal and compatible.
    config = types.LiveConnectConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=get_gemini_tools(),
        response_modalities=["AUDIO"],
    )

    # PyAudio for output
    pa = pyaudio.PyAudio()
    out_stream = pa.open(
        format=OUTPUT_FORMAT,
        channels=OUTPUT_CHANNELS,
        rate=OUTPUT_SAMPLE_RATE,
        output=True,
        frames_per_buffer=OUTPUT_CHUNK_SIZE,
    )

    tasks: list[asyncio.Task[Any]] = []
    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
            print("[OK] Connected to Gemini Live!", flush=True)
            print("Starting microphone, webcam, and screen capture...", flush=True)
            print("Agent is now listening and watching. Speak OR type a message and press Enter.\n", flush=True)

            send_queue: asyncio.Queue[dict] = asyncio.Queue()

            async def _mic_sender():
                async def send_chunk(data: bytes):
                    await send_queue.put({"type": "audio", "data": data})
                await stream_microphone_audio(send_chunk)

            async def _vision_sender():
                async def send_frame(b64: str):
                    await send_queue.put({"type": "video", "data": b64})
                await vision_loop(send_frame)

            async def _pump_send():
                """Batch and send queued messages to reduce API calls."""
                while True:
                    msg = await send_queue.get()
                    if msg["type"] == "audio":
                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=msg["data"],
                                mime_type=f"audio/pcm;rate={AUDIO_SAMPLE_RATE}",
                            ),
                        )
                    elif msg["type"] == "video":
                        img_bytes = base64.b64decode(msg["data"])
                        await session.send_realtime_input(
                            video=types.Blob(
                                data=img_bytes,
                                mime_type="image/jpeg",
                            ),
                        )
                    await asyncio.sleep(BATCH_DELAY)

            async def _text_input_sender():
                """Read text from stdin in a thread and send to session."""
                loop = asyncio.get_running_loop()
                while True:
                    text = await loop.run_in_executor(None, sys.stdin.readline)
                    text = text.strip()
                    if text:
                        print(f"[You]: {text}", flush=True)
                        try:
                            await session.send_client_content(
                                turns=types.Content(
                                    role="user",
                                    parts=[types.Part.from_text(text=text)],
                                ),
                                turn_complete=True,
                            )
                        except Exception as e:
                            print(f"[Error sending text]: {e}", flush=True)
                            # Fallback: try as realtime input
                            try:
                                await session.send_realtime_input(text=text)
                            except Exception as e2:
                                print(f"[Error with fallback]: {e2}", flush=True)

            async def _receive_loop():
                """Receive and process events from Gemini Live."""
                async for event in session.receive():
                    if hasattr(event, "tool_call") and event.tool_call:
                        for fc in event.tool_call.function_calls or []:
                            asyncio.create_task(_handle_tool_call(session, fc, memory_collection))

                    if hasattr(event, "server_content") and event.server_content:
                        sc = event.server_content
                        model_turn = getattr(sc, "model_turn", None)
                        parts = getattr(model_turn, "parts", None) or []
                        for part in parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                blob = part.inline_data
                                if blob and blob.data:
                                    _play_audio_chunk(out_stream, blob.data)
                            if hasattr(part, "text") and part.text:
                                print(f"[Agent]: {part.text}", flush=True)

            tasks = [
                asyncio.create_task(_pump_send()),
                asyncio.create_task(_text_input_sender()),
                asyncio.create_task(_receive_loop()),
            ]
            if ENABLE_MICROPHONE:
                tasks.append(asyncio.create_task(_mic_sender()))
            else:
                print("[Config] Microphone stream disabled.", flush=True)

            if ENABLE_WEBCAM or ENABLE_SCREEN_CAPTURE:
                tasks.append(asyncio.create_task(_vision_sender()))
            else:
                print("[Config] Vision stream disabled.", flush=True)
            await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        with contextlib.suppress(Exception):
            out_stream.stop_stream()
        with contextlib.suppress(Exception):
            out_stream.close()
        with contextlib.suppress(Exception):
            pa.terminate()


def main() -> None:
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
