#!/usr/bin/env python3
"""
Simple test to verify Gemini Live API response
"""
import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from config import LIVE_MODEL

load_dotenv()

async def test_live_response():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    client = genai.Client(api_key=api_key)
    
    model = LIVE_MODEL
    
    # Native-audio model requires AUDIO response modality
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
    )
    
    print(f"Connecting to {model}...")
    
    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            print("✅ Connected!")
            
            # Send a simple text message
            print("Sending: 'Hello, can you hear me?'")
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hello, can you hear me?")],
                ),
                turn_complete=True,
            )
            
            print("Waiting for response...")
            timeout = 10.0
            event_stream = session.receive()

            while True:
                try:
                    event = await asyncio.wait_for(event_stream.__anext__(), timeout=timeout)
                except asyncio.TimeoutError:
                    print("❌ Timeout - no response received")
                    break
                except StopAsyncIteration:
                    break
                
                print(f"Event received: {type(event).__name__}")
                
                if hasattr(event, "server_content") and event.server_content:
                    sc = event.server_content
                    model_turn = getattr(sc, "model_turn", None)
                    if model_turn:
                        parts = getattr(model_turn, "parts", None) or []
                        for part in parts:
                            if hasattr(part, "text") and part.text:
                                print(f"✅ Got text response: {part.text}")
                                return
                            if hasattr(part, "inline_data") and part.inline_data:
                                print(f"✅ Got audio response: {len(part.inline_data.data)} bytes")
                                return
                
                if hasattr(event, "setup_complete"):
                    print("Setup complete event received")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_response())
