#!/usr/bin/env python3
"""
Diagnostic tool to check what characters are in a tracker URL.
Helps verify that the URL decodes correctly.
"""

import sys
import os

# Add parent directory to path so gbfplanner can be imported
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from gbfplanner.decoder import decode_tracker_url, get_tracker_id_list
from gbfplanner.wiki import fetch_wiki_character_db
from gbfplanner.matcher import build_lookup

def main():
    print("=" * 60)
    print("GBF Tracker Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Get tracker ID list
    print("Fetching tracker character list...")
    id_list = get_tracker_id_list()
    if not id_list:
        print("✗ Failed to fetch tracker list")
        return
    print(f"✓ Tracker has {len(id_list)} characters")
    print()
    
    # Get wiki database
    print("Fetching wiki character database...")
    wiki_db = fetch_wiki_character_db()
    print(f"✓ Wiki has {len(wiki_db)} characters")
    print()
    
    # Get URL
    url = input("Enter your tracker URL (or press Enter to read from tracker_url.txt): ").strip()
    
    if not url:
        if os.path.exists('tracker_url.txt'):
            with open('tracker_url.txt', 'r') as f:
                url = f.read().strip()
            print(f"Read URL from tracker_url.txt ({len(url)} chars)")
        else:
            print("No URL provided and tracker_url.txt not found.")
            return
    
    print(f"\nAnalyzing URL ({len(url)} characters)...")
    print()
    
    # Extract hash
    if '#' in url:
        url_hash = url.split('#')[1]
    else:
        url_hash = url
    
    # Decode
    bitmask = decode_tracker_url(url_hash)
    if not bitmask:
        print("✗ Failed to decode URL")
        return
    
    # Count owned
    owned_indices = [i for i, bit in enumerate(bitmask) if bit == '1']
    total_owned = len(owned_indices)
    
    print(f"Total bits: {len(bitmask)}")
    print(f"Characters marked as owned: {total_owned}")
    print(f"Characters within ID list range: {len([i for i in owned_indices if i < len(id_list)])}")
    print()
    
    # Map to character IDs
    owned_ids = []
    for idx in owned_indices:
        if idx < len(id_list):
            owned_ids.append(id_list[idx])
    
    # Check for specific characters
    check_characters = {
        'Zeta (Water)': ['3040323000'],
        'Zeta (Dark)': ['3040112000', '3040628000'],
        'Zeta (Fire)': ['3040028000', '3040499000'],
        'Zeta (Light)': ['3040056000'],
    }
    
    print("Checking for specific characters:")
    print("-" * 40)
    for char_name, char_ids in check_characters.items():
        found = False
        for cid in char_ids:
            if cid in id_list:
                idx = id_list.index(cid)
                owned = idx in owned_indices
                if owned:
                    print(f"  ✓ {char_name} - OWNED (index {idx})")
                    found = True
                    break
        if not found:
            print(f"  ✗ {char_name} - NOT OWNED")
    print()
    
    # Show rarity breakdown
    ssr_count = len([cid for cid in owned_ids if cid.startswith('304')])
    sr_count = len([cid for cid in owned_ids if cid.startswith('303')])
    r_count = len([cid for cid in owned_ids if cid.startswith('302')])
    other_count = len(owned_ids) - ssr_count - sr_count - r_count
    
    print("Owned by rarity:")
    print(f"  SSR: {ssr_count}")
    print(f"  SR: {sr_count}")
    print(f"  R: {r_count}")
    print(f"  Other: {other_count}")
    print()
    
    # List first 20 owned SSRs
    print("First 20 owned SSR characters:")
    print("-" * 40)
    count = 0
    for cid in owned_ids:
        if cid.startswith('304') and cid in wiki_db:
            char = wiki_db[cid]
            print(f"  {char['name']} ({char['element']}) - {cid}")
            count += 1
            if count >= 20:
                print(f"  ... and {len(owned_ids) - count} more")
                break
    print()
    
    print("=" * 60)
    print("If characters are missing, your tracker URL may be truncated.")
    print("Try copying directly from browser's address bar with Ctrl+A")

if __name__ == "__main__":
    main()
