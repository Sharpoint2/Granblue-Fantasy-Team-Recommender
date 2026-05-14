#!/usr/bin/env python3
"""
Helper script to save gbf.wiki tracker URL to a file.
Run this after setting up your collection on the tracker page.
"""

import sys

def main():
    print("=" * 60)
    print("GBF Tracker URL Helper")
    print("=" * 60)
    print()
    print("This helps you save your tracker URL without truncation.")
    print()
    print("Method 1: Copy from browser address bar")
    print("  1. Go to https://gbf.wiki/Collection_Tracker")
    print("  2. Set up your collection")
    print("  3. Click the address bar, press Ctrl+A then Ctrl+C")
    print("  4. Paste below:")
    print()
    
    url = input("Paste your tracker URL: ").strip()
    
    if not url:
        print("No URL provided. Exiting.")
        return
    
    # Validate URL
    if 'gbf.wiki/Collection_Tracker' not in url:
        print("Warning: URL doesn't look like a gbf.wiki tracker URL")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Check length
    url_len = len(url)
    print(f"\nURL length: {url_len} characters")
    
    # Extract hash info
    if '#' in url:
        hash_part = url.split('#')[1]
        if '.' in hash_part:
            prefix = hash_part.split('.')[0]
            hash_b64 = hash_part.split('.')[1]
            print(f"Hash prefix: {prefix}")
            print(f"Hash length: {len(hash_b64)} characters")
            
            if len(hash_b64) < 300:
                print("\n⚠️  WARNING: Hash seems short! URL may be truncated.")
                print("Try copying directly from the browser's address bar.")
                print("Make sure to select ALL text (Ctrl+A) before copying.")
        elif ';' in hash_part:
            prefix = hash_part.split(';')[0]
            hash_b64 = hash_part.split(';')[1]
            print(f"Hash prefix: {prefix}")
            print(f"Hash length: {len(hash_b64)} characters")
    
    # Save to file
    filename = 'tracker_url.txt'
    try:
        with open(filename, 'w') as f:
            f.write(url)
        print(f"\n✓ Saved to {filename}")
        print(f"\nNow run: python3 planner.py")
        print("And just press Enter at the prompt to use the saved URL.")
    except Exception as e:
        print(f"\n✗ Error saving file: {e}")
        print(f"\nManually create {filename} and paste this URL:")
        print(url)

if __name__ == "__main__":
    main()
