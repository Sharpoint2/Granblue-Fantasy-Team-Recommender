#!/usr/bin/env python3
"""Show which characters couldn't be decoded."""

import base64
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from gbfplanner.decoder import get_tracker_id_list

# Get the URL
tracker_path = os.path.join(os.path.dirname(__file__), '..', 'tracker_url.txt')
if os.path.exists(tracker_path):
    with open(tracker_path, 'r') as f:
        url = f.read().strip()
else:
    url = input("Enter tracker URL: ").strip()

# Get tracker ID list
id_list = get_tracker_id_list(force_refresh=True)
if not id_list:
    print("Failed to fetch tracker list")
    exit(1)

print(f"Tracker has {len(id_list)} positions")
print(f"Mapped characters: {len([x for x in id_list if x is not None])}\n")

# Decode hash
hash_part = url.split('#')[1]
if '.' in hash_part:
    base64_string = hash_part.split('.')[1]
else:
    base64_string = hash_part

padding_needed = len(base64_string) % 4
if padding_needed:
    base64_string += '=' * (4 - padding_needed)

raw_bytes = base64.urlsafe_b64decode(base64_string)
bitmask = ''.join([format(byte, '08b') for byte in raw_bytes])

# Find owned positions
owned_positions = []
for position in range(len(id_list)):
    bit_start = position * 3
    bit_end = bit_start + 3
    if bit_end > len(bitmask):
        break
    char_bits = bitmask[bit_start:bit_end]
    if '1' in char_bits:
        owned_positions.append(position)

# Find positions with bits set but no character mapped
unmapped = []
for position in range(len(id_list), len(bitmask) // 3):
    bit_start = position * 3
    bit_end = bit_start + 3
    if bit_end > len(bitmask):
        break
    char_bits = bitmask[bit_start:bit_end]
    if '1' in char_bits:
        unmapped.append(position)

print(f"Total owned characters: {len(owned_positions)}")
print(f"Unmapped positions (beyond tracker list): {len(unmapped)}")

if unmapped:
    print(f"\nPositions without character data: {unmapped[:20]}")
    if len(unmapped) > 20:
        print(f"  ... and {len(unmapped) - 20} more")

# Calculate expected total
total_set_bits = bitmask.count('1')
print(f"\nTotal set bits in hash: {total_set_bits}")
print(f"Expected characters (bits/3): {total_set_bits // 3}")
