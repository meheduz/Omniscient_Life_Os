#!/usr/bin/env python3
"""
Health check utility for Omniscient Life OS
Verifies all dependencies and configurations
"""

import os
import sys
from pathlib import Path

from config import (
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_SAMPLE_RATE,
    MEMORY_PERSIST_DIR,
)

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False

def check_dependencies():
    """Check required packages"""
    required = [
        ("google.genai", "google-genai"),
        ("websockets", "websockets"),
        ("cv2", "opencv-python"),
        ("mss", "mss"),
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
        ("numpy", "numpy"),
        ("PIL", "Pillow"),
        ("dotenv", "python-dotenv"),
    ]
    
    optional = [
        ("pyaudio", "pyaudio"),
    ]
    
    print("\n📦 Checking dependencies:")
    all_good = True
    
    for module, package in required:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (required)")
            all_good = False
    
    for module, package in optional:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ⚠️  {package} (optional, needed for audio)")
    
    return all_good

def check_api_key():
    """Check for API key"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        print("\n✅ API key found")
        return True
    else:
        print("\n❌ API key not found")
        print("   Set GEMINI_API_KEY in .env file")
        return False

def check_camera():
    """Check camera access"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                print("\n✅ Camera accessible")
                return True
            else:
                print("\n⚠️  Camera opened but can't read frames")
                return False
        else:
            print("\n⚠️  Camera not accessible (may need permissions)")
            return False
    except Exception as e:
        print(f"\n❌ Camera error: {e}")
        return False

def check_microphone():
    """Check microphone access"""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        # Try to open input stream
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=AUDIO_CHANNELS,
                rate=AUDIO_SAMPLE_RATE,
                input=True,
                frames_per_buffer=AUDIO_CHUNK_SIZE,
            )
            stream.close()
            p.terminate()
            print("✅ Microphone accessible")
            return True
        except Exception:
            p.terminate()
            print("⚠️  Microphone not accessible (may need permissions)")
            return False
    except ImportError:
        print("⚠️  PyAudio not installed (microphone won't work)")
        return False

def check_memory_db():
    """Check ChromaDB"""
    db_path = Path(MEMORY_PERSIST_DIR)
    if db_path.exists():
        try:
            from memory import get_memory_client, get_collection
            client = get_memory_client()
            collection = get_collection(client)
            count = collection.count()
            print(f"\n✅ Memory database: {count} entries")
            return True
        except Exception as e:
            print(f"\n❌ Memory database error: {e}")
            return False
    else:
        print("\n✅ Memory database will be created on first run")
        return True

def check_disk_space():
    """Check available disk space"""
    import shutil
    total, used, free = shutil.disk_usage(".")
    free_gb = free / (1024**3)
    
    if free_gb > 1:
        print(f"\n✅ Disk space: {free_gb:.1f} GB free")
        return True
    else:
        print(f"\n⚠️  Low disk space: {free_gb:.1f} GB free")
        return False

def test_api_connection():
    """Test Gemini API connection"""
    try:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("\n⚠️  Skipping API test (no key)")
            return False
        
        client = genai.Client(api_key=api_key)
        # Just list models to verify connection
        list(client.models.list())
        print("\n✅ API connection successful")
        return True
    except Exception as e:
        print(f"\n❌ API connection failed: {e}")
        return False

def main():
    print("🏥 Omniscient Life OS - Health Check\n")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("API Key", check_api_key),
        ("API Connection", test_api_connection),
        ("Camera", check_camera),
        ("Microphone", check_microphone),
        ("Memory Database", check_memory_db),
        ("Disk Space", check_disk_space),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("\n📊 Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to run.")
        print("\nStart the agent with: ./start.sh")
    else:
        print("\n⚠️  Some checks failed. Review the issues above.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Set API key in .env file")
        print("  - Grant camera/microphone permissions in System Settings")
        print("  - Install PyAudio: brew install portaudio && pip install pyaudio")

if __name__ == "__main__":
    main()
