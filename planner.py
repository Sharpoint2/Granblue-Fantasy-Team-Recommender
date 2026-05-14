#!/usr/bin/env python3
"""
GBF Team Planner - Main entry point.

Recommends team compositions based on your gbf.wiki Collection Tracker.
"""

import json
import os

from gbfplanner.decoder import decode_tracker_url, get_tracker_id_list, clear_tracker_cache
from gbfplanner.wiki import fetch_wiki_character_db
from gbfplanner.matcher import (
    build_lookup,
    matches_character_spec,
    get_character_display_name,
    generate_team_recommendations,
    get_owned_flex_options,
)


# ==========================================
# 1. Parse User's Collection
# ==========================================
def get_owned_characters(tracker_url=None, id_list=None):
    """
    Parses the user's roster from a gbf.wiki tracker URL.
    Decodes the Base64 bitmask and maps owned characters by wiki ID.
    Accepts both full URLs and just the hash portion.
    If no URL is provided, returns a fallback list of owned characters.
    """
    if tracker_url:
        print("Decoding tracker URL...")
        
        # Extract hash from full URL if needed
        url_hash = tracker_url
        if '#' in tracker_url:
            url_hash = tracker_url.split('#')[1]
        
        bitmask = decode_tracker_url(url_hash)
        
        if not bitmask:
            print("Failed to decode tracker URL. Using fallback roster.")
            return _get_fallback_roster()
        
        lookup_list = id_list if id_list is not None else get_tracker_id_list()
        
        if lookup_list is None:
            print("Error: Could not get character ID list from tracker.")
            return _get_fallback_roster()
        
        owned_ids = set()
        total_marked = 0
        
        for position, char_id in enumerate(lookup_list):
            if char_id is None:
                continue
            
            bit_start = position * 3
            bit_end = bit_start + 3
            
            if bit_end > len(bitmask):
                break
            
            char_bits = bitmask[bit_start:bit_end]
            if '1' in char_bits:
                owned_ids.add(char_id)
                total_marked += 1
        
        total_set_bits = bitmask.count('1')
        unmapped_bits = total_set_bits - sum(
            1 for pos in range(len(lookup_list))
            if lookup_list[pos] is not None and '1' in bitmask[pos*3:(pos+1)*3]
        )
        
        if unmapped_bits > 0:
            print(f"  Note: {unmapped_bits} ownership bits are beyond the current tracker list")
            print(f"  Tracker has {len([x for x in lookup_list if x is not None])} characters")
            print(f"  Hash contains data for {total_marked} owned characters")
        
        print(f"Decoded {len(owned_ids)} owned characters from tracker.")
        return owned_ids
    else:
        print("Loading fallback owned characters...")
        return _get_fallback_roster()


def _get_fallback_roster():
    """Fallback list of owned characters for when no tracker URL is provided."""
    return [
        "3040492000",  # Gabriel (Water)
        {"name": "Zeta", "element": "Fire"},
        "3040348000",  # Poseidon (Water)
        {"name": "Haaselia", "element": "Water"},
        {"name": "Vajra", "element": "Water"},
        "3040502000",  # Payila (Water)
        "3040406000",  # Gwynne (Water)
    ]


# ==========================================
# 2. Load Teams Database
# ==========================================
def load_teams_database():
    """Load teams from the data/teams_database.json file."""
    db_file = os.path.join(os.path.dirname(__file__), 'data', 'teams_database.json')
    
    if not os.path.exists(db_file):
        return []
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        teams = db.get('teams', [])
        
        converted = []
        for team in teams:
            converted_team = {
                'team_name': team.get('team_name', 'Unknown'),
                'element': team.get('element', 'Unknown'),
                'description': team.get('description', ''),
                'core_characters': [],
                'flex_options': []
            }
            
            for char in team.get('characters', []):
                if isinstance(char, dict):
                    if char.get('element'):
                        converted_team['core_characters'].append({
                            'name': char['name'],
                            'element': char['element']
                        })
                    else:
                        converted_team['core_characters'].append(char['name'])
                else:
                    converted_team['core_characters'].append(char)
            
            for char in team.get('flex_slots', []):
                if isinstance(char, dict):
                    if char.get('element'):
                        converted_team['flex_options'].append({
                            'name': char['name'],
                            'element': char['element']
                        })
                    else:
                        converted_team['flex_options'].append(char['name'])
                else:
                    converted_team['flex_options'].append(char)
            
            converted.append(converted_team)
        
        return converted
        
    except Exception as e:
        print(f"Warning: Could not load teams database: {e}")
        return []


def get_recommended_teams():
    """Built-in recommended team compositions."""
    return [
        {
            "team_name": "Water GW Burst (Relic Buster)",
            "element": "Water",
            "core_characters": [
                {"name": "Zeta", "element": "Water"},
                {"name": "Gabriel", "element": "Water"},
                {"name": "Haaselia", "element": "Water"}
            ],
            "flex_options": [
                {"name": "Poseidon", "element": "Water"},
                {"name": "Gwynne", "element": "Water"}
            ],
            "description": "Standard 1-turn burst setup for Guild Wars EX+."
        },
        {
            "team_name": "Water Hard Raid Kengo",
            "element": "Water",
            "core_characters": [
                {"name": "Vajra", "element": "Water"},
                {"name": "Haaselia", "element": "Water"},
                {"name": "Payila", "element": "Water"}
            ],
            "flex_options": [
                {"name": "Gabriel", "element": "Water"},
                {"name": "Lucio", "element": "Water"}
            ],
            "description": "Ougi-spam team for clearing high-difficulty content."
        },
        {
            "team_name": "Fire Skill Damage",
            "element": "Fire",
            "core_characters": [
                {"name": "Medusa", "element": "Fire"},
                {"name": "Percival", "element": "Fire"},
                {"name": "Michael", "element": "Fire"}
            ],
            "flex_options": [
                {"name": "Anderson", "element": "Fire"},
                {"name": "Zeta", "element": "Fire"}
            ],
            "description": "Standard Fire skill-spam setup."
        }
    ]


# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    print("GBF Team Planner")
    print("=" * 60)
    print()
    print("How to provide your tracker URL:")
    print("1. Paste the full URL directly (if your terminal supports it)")
    print("2. Save the URL to a file named 'tracker_url.txt' and press Enter")
    print("3. Enter 'file:<path>' to read from a custom file")
    print()
    
    input_text = input("Enter your gbf.wiki tracker URL (or press Enter for options): ").strip()
    
    tracker_url = None
    
    if not input_text:
        if os.path.exists('tracker_url.txt'):
            try:
                with open('tracker_url.txt', 'r') as f:
                    tracker_url = f.read().strip()
                print(f"Read URL from tracker_url.txt ({len(tracker_url)} characters)\n")
            except Exception as e:
                print(f"Error reading tracker_url.txt: {e}")
                tracker_url = None
        else:
            print("No URL provided and tracker_url.txt not found.")
            print("Using fallback roster.\n")
    elif input_text.startswith('file:'):
        filepath = input_text[5:]
        try:
            with open(filepath, 'r') as f:
                tracker_url = f.read().strip()
            print(f"Read URL from {filepath} ({len(tracker_url)} characters)\n")
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            tracker_url = None
    else:
        tracker_url = input_text
        print(f"Using provided URL ({len(tracker_url)} characters)\n")
    
    if tracker_url:
        hash_part = tracker_url.split('#')[-1] if '#' in tracker_url else tracker_url
        if '.' in hash_part:
            hash_len = len(hash_part.split('.')[1]) if '.' in hash_part else 0
        elif ';' in hash_part:
            hash_len = len(hash_part.split(';')[1]) if ';' in hash_part else 0
        else:
            hash_len = len(hash_part)
        
        print(f"  Hash portion length: {hash_len} characters")
        if hash_len < 300:
            print(f"  WARNING: Hash seems short (expected ~324 chars). URL may be truncated!")
            print(f"  Try saving to a file instead of pasting directly.")
        print()
    
    wiki_db = fetch_wiki_character_db()
    
    clear_tracker_cache()
    tracker_id_list = get_tracker_id_list()
    
    my_roster = get_owned_characters(tracker_url, tracker_id_list)
    
    def is_character_id(s):
        return isinstance(s, str) and s.startswith('304') and s.isdigit()
    
    if wiki_db and my_roster:
        sample = next(iter(my_roster))
        if not is_character_id(sample):
            name_to_ids, id_to_char, name_element_to_ids = build_lookup(wiki_db)
            
            my_roster_ids = set()
            for spec in my_roster:
                if isinstance(spec, str) and spec in wiki_db:
                    my_roster_ids.add(spec)
                elif isinstance(spec, dict):
                    name = spec.get('name')
                    element = spec.get('element')
                    if element and (name, element) in name_element_to_ids:
                        my_roster_ids.update(name_element_to_ids[(name, element)])
                    elif name in name_to_ids:
                        my_roster_ids.update(name_to_ids[name])
                    else:
                        print(f"  Warning: '{name}' not found in wiki database")
                elif isinstance(spec, str):
                    if spec in name_to_ids:
                        my_roster_ids.update(name_to_ids[spec])
                    else:
                        print(f"  Warning: '{spec}' not found in wiki database")
            
            my_roster = my_roster_ids
            print(f"Converted fallback roster to {len(my_roster)} character IDs.\n")
    
    meta_teams = get_recommended_teams()
    
    database_teams = load_teams_database()
    if database_teams:
        meta_teams.extend(database_teams)
        print(f"Loaded {len(database_teams)} teams from database\n")
    
    recommended = generate_team_recommendations(my_roster, meta_teams, wiki_db)
    
    print("--- RECOMMENDED TEAMS BASED ON YOUR ROSTER ---")
    for idx, team in enumerate(recommended, 1):
        print(f"\n{idx}. {team['team_name']} ({team['element']})")
        core_display = [get_character_display_name(spec) for spec in team['core_characters']]
        print(f"   Core: {', '.join(core_display)}")
        print(f"   Desc: {team['description']}")
        
        owned_flex = get_owned_flex_options(team, my_roster, wiki_db)
        if owned_flex:
            print(f"   Owned Flex Options: {', '.join(owned_flex)}")
