import base64
import cloudscraper
import re

def fetch_tracker_id_list():
    """Fetches the character ID list from gbf.wiki Collection Tracker page.
    
    Returns a list where index = bit position in hash, value = character ID.
    Extended to 1944 entries to handle all possible indices.
    """
    scraper = cloudscraper.create_scraper()
    url = "https://gbf.wiki/Collection_Tracker"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = scraper.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Extract all tracker-item divs and their data attributes
        divs = re.findall(r'<div class="tracker-item[^"]*"([^>]+)>', response.text)
        
        items = []
        for div in divs:
            type_match = re.search(r'data-type="([^"]+)"', div)
            short_match = re.search(r'data-short-id="(\d+)"', div)
            id_match = re.search(r'data-id="(\d+)"', div)
            
            if type_match and short_match and id_match:
                items.append((type_match.group(1), short_match.group(1), id_match.group(1)))
        
        print(f"  Extracted {len(items)} items from tracker page")
        
        if not items:
            # Fallback: just get data-id in order
            ids = re.findall(r'<div class="tracker-item[^"]*"[^>]*data-id="(\d+)"', response.text)
            # Extend to 1944 entries with None for missing indices
            extended = ids + [None] * (1944 - len(ids))
            return extended[:1944]
        
        # Build mapping from position to character ID
        # The hash uses separate base64 strings per group (c4, c3, c2, s4, s3, s2)
        # Within each group, characters are at positions based on their short_id index
        # Each character uses 3 bits in the base64-decoded bytes
        
        # Get max index for each group
        max_indices = {}
        for item_type, short_id, char_id in items:
            rarity = int(short_id[0])
            index = int(short_id[1:])
            key = (item_type, rarity)
            if key not in max_indices or index > max_indices[key]:
                max_indices[key] = index
        
        print(f"  Max indices by group: {max_indices}")
        
        # Calculate byte offsets for each group in the concatenated hash
        # Each group uses: ((max_index // 8) + 1) * 3 bytes
        group_info = {}
        current_byte = 0
        for key in [('c', 4), ('c', 3), ('c', 2), ('s', 4), ('s', 3), ('s', 2)]:
            if key in max_indices:
                max_idx = max_indices[key]
                group_bytes = ((max_idx // 8) + 1) * 3
                group_info[key] = {
                    'start_byte': current_byte,
                    'size_bytes': group_bytes,
                    'max_index': max_idx
                }
                current_byte += group_bytes
            else:
                group_info[key] = {
                    'start_byte': current_byte,
                    'size_bytes': 0,
                    'max_index': -1
                }
        
        print(f"  Total bytes: {current_byte}")
        
        # Create a flat list where index = position in the combined hash
        # Each position corresponds to 3 bits in the hash
        max_position = (current_byte * 8) // 3 + 1
        result = [None] * max_position
        
        # Map each item to its position
        for item_type, short_id, char_id in items:
            rarity = int(short_id[0])
            index = int(short_id[1:])
            key = (item_type, rarity)
            
            if key in group_info:
                info = group_info[key]
                # Calculate byte position within group
                byte_in_group = (index // 8) * 3
                bit_in_byte = (index % 8) * 3
                
                # Calculate absolute bit position
                absolute_bit = (info['start_byte'] + byte_in_group) * 8 + bit_in_byte
                
                # Convert to position index (each position is 3 bits)
                position = absolute_bit // 3
                
                if position < len(result):
                    result[position] = char_id
        
        return result
        
    except Exception as e:
        print(f"Warning: Failed to fetch tracker ID list: {e}")
        import traceback
        traceback.print_exc()
        return None

# Cache for the ID list
_cached_id_list = None

def get_tracker_id_list(force_refresh=False):
    """Get the tracker ID list, fetching it if necessary."""
    global _cached_id_list
    if _cached_id_list is None or force_refresh:
        _cached_id_list = fetch_tracker_id_list()
    return _cached_id_list

def clear_tracker_cache():
    """Clear the cached ID list to force a fresh fetch next time."""
    global _cached_id_list
    _cached_id_list = None
    print("Tracker ID list cache cleared.")

def calculate_bit_position(group_start, index_within_group):
    """Calculate bit position from group start and index.
    
    Each group of 8 items uses 3 bytes (24 bits).
    Each item within the group uses 3 bits.
    """
    group_byte = (index_within_group // 8) * 3
    bit_offset = (index_within_group % 8) * 3
    return group_start * 8 + group_byte * 8 + bit_offset  # Convert to bit position

def decode_tracker_url(url_hash):
    """Decodes the gbf.wiki collection tracker base64 hash into a binary bitmask."""
    print(f"Original Hash: {url_hash}")
    
    # Clean the hash
    if ';' in url_hash:
        base64_string = url_hash.split(';')[1]
    elif '.' in url_hash:
        base64_string = url_hash.split('.')[1]
    else:
        base64_string = url_hash

    # Add padding if needed
    padding_needed = len(base64_string) % 4
    if padding_needed:
        base64_string += '=' * (4 - padding_needed)

    try:
        raw_bytes = base64.urlsafe_b64decode(base64_string)
        bitmask = ''.join([format(byte, '08b') for byte in raw_bytes])
        return bitmask
    except Exception as e:
        print(f"Error decoding URL: {e}")
        return None

if __name__ == "__main__":
    id_list = get_tracker_id_list()
    if id_list:
        print(f"Successfully fetched {len(id_list)} character IDs from tracker")
        if hasattr(id_list, '_group_info'):
            print("Group info:", id_list._group_info)
