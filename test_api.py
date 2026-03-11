"""Test Gemini API connectivity and available models."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ No API key found!")
        exit(1)
    
    print(f"✓ API key loaded: {api_key[:20]}...")
    
    client = genai.Client(api_key=api_key)
    print("✓ Client created successfully")
    
    # Try listing available models
    print("\nAttempting to list models...")
    try:
        models = client.models.list()
        print("\n✅ Available models:")
        for model in models:
            if hasattr(model, 'name'):
                print(f"  - {model.name}")
                if hasattr(model, 'supported_generation_methods'):
                    print(f"    Methods: {model.supported_generation_methods}")
    except Exception as e:
        print(f"Could not list models: {e}")
    
    # Try a simple generation test
    print("\n\nTesting basic text generation...")
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Say 'Hello' if you can hear me."
        )
        print(f"✅ Basic generation works: {response.text[:100]}")
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
