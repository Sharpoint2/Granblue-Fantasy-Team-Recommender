"""GBF Wiki Cargo API interactions."""

import importlib
import requests

try:
    cloudscraper = importlib.import_module("cloudscraper")
except ImportError:
    cloudscraper = None

# Prefer cloudscraper when available; fall back to requests so execution never fails.
if cloudscraper is not None:
    scraper = cloudscraper.create_scraper()
else:
    print("Warning: cloudscraper is not installed in this Python environment. Falling back to requests.")
    scraper = requests.Session()


def fetch_wiki_character_db(rarities=None):
    """Fetches characters from the GBF Wiki Cargo API with pagination.
    
    Args:
        rarities: List of rarities to fetch (e.g., ['SSR'], ['SSR', 'SR'], etc.)
                 If None, fetches all rarities.
    
    Returns:
        Dict mapping character ID to character data
    """
    if rarities is None:
        rarities = ['SSR', 'SR', 'R']
    
    print(f"Fetching character database from gbf.wiki ({', '.join(rarities)})...")
    url = "https://gbf.wiki/api.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }

    char_db = {}
    
    for rarity in rarities:
        offset = 0
        limit = 500
        rarity_fetched = 0

        while True:
            params = {
                'action': "cargoquery",
                'tables': "characters",
                'fields': "name,id,element",
                'where': f"rarity='{rarity}'",
                'format': "json",
                'limit': str(limit),
                'offset': str(offset)
            }

            try:
                response = scraper.get(url, params=params, timeout=15, headers=headers)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                print(f"Warning: Failed to fetch {rarity} data ({exc}).")
                break

            if 'cargoquery' not in data or not data['cargoquery']:
                break

            for entry in data['cargoquery']:
                char = entry['title']
                char_id = char['id']
                char_db[char_id] = {
                    'name': char['name'],
                    'element': char['element'],
                    'rarity': rarity
                }
            
            batch_size = len(data['cargoquery'])
            rarity_fetched += batch_size
            
            if batch_size < limit:
                break
            
            offset += limit
        
        print(f"  Fetched {rarity_fetched} {rarity} characters.")

    print(f"Total: {len(char_db)} characters from wiki.")
    return char_db
