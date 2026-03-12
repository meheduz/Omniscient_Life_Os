#!/usr/bin/env python3
"""
Cleanup and optimization utility for Omniscient Life OS
"""

import os
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

def get_dir_size(path):
    """Calculate directory size in MB"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    except Exception:
        pass
    return total / (1024 * 1024)

def cleanup_cache():
    """Remove Python cache files"""
    print("🧹 Cleaning Python cache...")
    count = 0
    for root, dirs, files in os.walk(PROJECT_DIR):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            shutil.rmtree(cache_dir)
            count += 1
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                count += 1
    print(f"✅ Removed {count} cache files")

def optimize_chroma():
    """Optimize ChromaDB"""
    chroma_dir = PROJECT_DIR / "chroma_db"
    if chroma_dir.exists():
        size_before = get_dir_size(chroma_dir)
        print(f"📊 ChromaDB size: {size_before:.2f} MB")
        
        # Import and optimize
        try:
            from memory import get_memory_client, get_collection
            client = get_memory_client()
            collection = get_collection(client)
            count = collection.count()
            print(f"📝 Memory entries: {count}")
            
            if count > 1000:
                print("⚠️  Large memory database. Consider archiving old entries.")
        except Exception as e:
            print(f"❌ Error optimizing ChromaDB: {e}")
    else:
        print("ℹ️  No ChromaDB found")

def show_disk_usage():
    """Show disk usage breakdown"""
    print("\n📊 Disk Usage:")
    
    dirs_to_check = [
        (".venv", "Virtual Environment"),
        ("chroma_db", "Memory Database"),
        ("__pycache__", "Python Cache"),
    ]
    
    for dir_name, label in dirs_to_check:
        dir_path = PROJECT_DIR / dir_name
        if dir_path.exists():
            size = get_dir_size(dir_path)
            print(f"  {label}: {size:.2f} MB")

def main():
    print("🔧 Omniscient Life OS - Cleanup & Optimization\n")
    
    show_disk_usage()
    print()
    
    cleanup_cache()
    optimize_chroma()
    
    print("\n✅ Cleanup complete!")
    print("\nOptimization tips:")
    print("  - Adjust VISION_INTERVAL in config.py to reduce API calls")
    print("  - Lower JPEG_QUALITY for smaller payloads")
    print("  - Archive old memory entries if database is large")

if __name__ == "__main__":
    main()
