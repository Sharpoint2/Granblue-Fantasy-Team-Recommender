#!/usr/bin/env python3
"""
Comprehensive scraper for GBF team recommendations from Kamigame and Gamewith.
Builds a complete team database for all characters using gbf.wiki name mapping.
"""

import cloudscraper
import json
import time
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from datetime import datetime

class GBFTeamScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.wiki_db = {}
        self.jpname_map = {}
        self.name_element_map = {}  # (jpname, element) -> list of chars
        self.teams_db = {
            "version": "1.1",
            "last_updated": "",
            "teams": [],
            "characters": {}
        }
        self.kamigame_base = "https://kamigame.jp/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB"
        self.gamewith_base = "https://xn--bck3aza1a2if6kra4ee0hf.gamewith.jp"
        
        # Common name transformations for kamigame/gamewith -> gbf.wiki jpname
        self.name_transforms = {
            'ジーク': 'ジークフリート',
            'リミゼタ': 'ゼタ',
            'クリゼタ': 'ゼタ',
            '水着ゼタ': 'ゼタ',
            '水ゼタ': 'ゼタ',
            'リミパー': 'パーシヴァル',
            '浴衣アグロ': 'アグロヴァル',
            '火ジーク': 'ジークフリート',
            '浴衣ナタク': 'ナタク',
            '義賊': '主人公',  # Main character/job
            'スパルタ': '主人公',
            'レリバ': '主人公',
            '黒猫道士': '主人公',
            'マナダイバー': '主人公',
            'ランサーオリ': '主人公',
            'スマヒヒト': '主人公',
            'クリュサオル': '主人公',
        }
        
        # Element mapping
        self.element_map = {
            '火': 'Fire',
            '水': 'Water',
            '土': 'Earth',
            '風': 'Wind',
            '光': 'Light',
            '闇': 'Dark',
        }
        
        # Special version hints
        self.version_hints = {
            '水着': 'Water',
            '浴衣': 'Fire',
            'クリスマス': 'Dark',
            'ハロウィン': 'Dark',
            'バレンタイン': 'Fire',
            '十二神将': None,  # Keep original element
            'リミテッド': None,
        }
    
    def fetch_wiki_database(self):
        """Fetch all characters from gbf.wiki Cargo API."""
        print("Fetching character database from gbf.wiki...")
        url = "https://gbf.wiki/api.php"
        
        for rarity in ['SSR', 'SR', 'R']:
            offset = 0
            limit = 500
            count = 0
            
            while True:
                params = {
                    'action': 'cargoquery',
                    'tables': 'characters',
                    'fields': 'name,jpname,id,element',
                    'where': f'rarity="{rarity}"',
                    'format': 'json',
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                try:
                    response = self.scraper.get(url, params=params, timeout=30)
                    data = response.json()
                except Exception as e:
                    print(f"  Error fetching {rarity}: {e}")
                    break
                
                if 'cargoquery' not in data or not data['cargoquery']:
                    break
                
                for entry in data['cargoquery']:
                    char = entry['title']
                    char_id = char['id']
                    self.wiki_db[char_id] = {
                        'name': char['name'],
                        'jpname': char.get('jpname', ''),
                        'element': char.get('element', 'Unknown')
                    }
                    count += 1
                
                if len(data['cargoquery']) < limit:
                    break
                offset += limit
            
            print(f"  Fetched {count} {rarity} characters.")
        
        print(f"Total wiki characters: {len(self.wiki_db)}")
        self._build_name_mappings()
        return len(self.wiki_db)
    
    def _build_name_mappings(self):
        """Build Japanese name to English character mappings."""
        self.jpname_map = {}
        self.name_element_map = {}
        
        for char_id, char in self.wiki_db.items():
            jp = char.get('jpname', '')
            if not jp:
                continue
            
            if jp not in self.jpname_map:
                self.jpname_map[jp] = []
            self.jpname_map[jp].append(char)
            
            key = (jp, char.get('element', 'Unknown'))
            if key not in self.name_element_map:
                self.name_element_map[key] = []
            self.name_element_map[key].append(char)
        
        print(f"Built name mappings: {len(self.jpname_map)} unique JP names")
    
    def resolve_japanese_name(self, jp_name, page_element_hint=None):
        """
        Resolve a Japanese character name from kamigame/gamewith to English.
        Returns dict with 'name', 'element', 'id' or None if not found.
        """
        if not jp_name or jp_name in ['主人公', '義賊', 'スパルタ', 'レリバ', '黒猫道士', 'マナダイバー', 'ランサーオリ', 'スマヒヒト', 'クリュサオル']:
            return None  # Skip main character/job names
        
        # Remove common prefixes/suffixes and clean up
        clean_name = jp_name.strip()
        
        # Extract element hint from suffix like （火）, (火)
        element_hint = None
        version_hint = None
        
        suffix_match = re.search(r'[（(](.+?)[）)]', clean_name)
        if suffix_match:
            suffix = suffix_match.group(1)
            if suffix in self.element_map:
                element_hint = self.element_map[suffix]
            elif suffix in self.version_hints:
                version_hint = suffix
            clean_name = re.sub(r'[（(].*?[）)]', '', clean_name).strip()
        
        # Check for element prefix like 火ジーク
        for jp_elem, en_elem in self.element_map.items():
            if clean_name.startswith(jp_elem) and len(clean_name) > len(jp_elem):
                element_hint = en_elem
                clean_name = clean_name[len(jp_elem):]
                break
        
        # Apply name transformations
        if clean_name in self.name_transforms:
            clean_name = self.name_transforms[clean_name]
        
        # Look up in mapping
        candidates = self.jpname_map.get(clean_name, [])
        
        if not candidates:
            # Try stripping honorifics or common suffixes
            for suffix in ['さん', 'くん', 'ちゃん', '様']:
                if clean_name.endswith(suffix):
                    alt_name = clean_name[:-len(suffix)]
                    if alt_name in self.jpname_map:
                        candidates = self.jpname_map[alt_name]
                        break
        
        if not candidates:
            return None
        
        # Disambiguate using element hints
        if len(candidates) == 1:
            return candidates[0]
        
        # Multiple candidates - use hints to pick
        target_element = element_hint or page_element_hint
        
        # If version hint maps to an element, use it
        if version_hint and self.version_hints.get(version_hint):
            target_element = self.version_hints[version_hint]
        
        if target_element:
            for c in candidates:
                if c.get('element') == target_element:
                    return c
        
        # Return first candidate as fallback
        return candidates[0]
    
    # ==================== KAMIGAME SCRAPER ====================
    
    def scrape_kamigame_character_list(self):
        """Fetch all character page URLs from kamigame."""
        url = f"{self.kamigame_base}/%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC/index.html"
        print(f"\nFetching kamigame character list...")
        
        try:
            response = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a', href=True)
            seen_urls = set()
            char_urls = []
            
            for link in links:
                href = link['href']
                if '/%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC/' in href and href.endswith('.html'):
                    # Deduplicate by URL
                    full_url = urljoin(f"{self.kamigame_base}/", href)
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    # Get the character name from URL
                    decoded = unquote(href)
                    name_part = decoded.split('/')[-1].replace('.html', '')
                    # Remove SSR/SR/R prefix
                    name_part = re.sub(r'^(SSR|SR|R)', '', name_part)
                    
                    char_urls.append({
                        'jp_name': name_part,
                        'url': full_url
                    })
            
            print(f"Found {len(char_urls)} unique character pages on kamigame")
            return char_urls
            
        except Exception as e:
            print(f"Error fetching kamigame character list: {e}")
            return []
    
    def scrape_kamigame_character_page(self, char_url, char_jp_name):
        """Scrape team compositions from a single kamigame character page."""
        teams = []
        
        try:
            response = self.scraper.get(char_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Determine page element from title or content
            title = soup.title.string if soup.title else ''
            page_element = self._detect_element_from_text(title)
            
            # If title doesn't have element, try to infer from the character being scraped
            if not page_element:
                resolved_char = self.resolve_japanese_name(char_jp_name)
                if resolved_char:
                    page_element = resolved_char.get('element')
            
            # Find team composition sections
            # Look for headers containing "編成" (formation/team)
            headers = soup.find_all(['h2', 'h3', 'h4'])
            
            for header in headers:
                header_text = header.get_text(strip=True)
                
                # Skip non-team headers
                if not any(k in header_text for k in ['編成', 'パーティ', 'チーム', '運用']):
                    continue
                if any(k in header_text for k in ['目次', '関連', 'おすすめ記事', 'カテゴリ']):
                    continue
                
                # This is a team section - extract characters
                team_chars = []
                team_desc = []
                
                # Get content until next h2 or h3
                current = header.find_next_sibling()
                depth = 0
                while current and current.name not in ['h2'] and depth < 20:
                    if current.name in ['div', 'p', 'table', 'ul']:
                        text = current.get_text(strip=True)
                        if text and len(text) > 5:
                            team_desc.append(text[:300])
                        
                        # Look for character images
                        imgs = current.find_all('img', alt=True)
                        for img in imgs:
                            alt = img.get('alt', '').strip()
                            # Skip non-character images
                            if not alt or any(skip in alt for skip in [
                                'グラブル', '編成', '武器', '召喚石', 'スキル', 'アビリティ',
                                '入手方法', '効果', '評価', '攻略', 'まとめ', '画像'
                            ]):
                                continue
                            # Skip if it looks like a weapon/summon name (too long or specific patterns)
                            if len(alt) > 20 and 'の' in alt:
                                continue
                            
                            resolved = self.resolve_japanese_name(alt, page_element)
                            if resolved and resolved['name'] not in [c['name'] for c in team_chars]:
                                team_chars.append({
                                    'name': resolved['name'],
                                    'element': resolved.get('element', 'Unknown'),
                                    'role': 'Core'
                                })
                    
                    current = current.find_next_sibling()
                    depth += 1
                
                if len(team_chars) >= 2:  # Need at least 2 characters for a team
                    team_name = f"{char_jp_name} - {header_text}"
                    description = ' '.join(team_desc[:2])[:300] if team_desc else ''
                    
                    teams.append({
                        'team_name': team_name,
                        'element': page_element or 'Unknown',
                        'source': 'kamigame',
                        'source_url': char_url,
                        'characters': team_chars,
                        'description': description
                    })
            
            return teams
            
        except Exception as e:
            print(f"  Error scraping {char_url}: {e}")
            return []
    
    def _detect_element_from_text(self, text):
        """Detect GBF element from Japanese text."""
        if not text:
            return None
        for jp, en in self.element_map.items():
            if jp in text:
                return en
        return None
    
    def scrape_kamigame_all(self, max_chars=None):
        """Scrape all kamigame character pages for team data."""
        print("\n" + "="*60)
        print("SCRAPING KAMIGAME")
        print("="*60)
        
        char_list = self.scrape_kamigame_character_list()
        if not char_list:
            return 0
        
        if max_chars:
            char_list = char_list[:max_chars]
        
        total_teams = 0
        for i, char_info in enumerate(char_list):
            print(f"\n[{i+1}/{len(char_list)}] {char_info['jp_name']}")
            teams = self.scrape_kamigame_character_page(char_info['url'], char_info['jp_name'])
            
            if teams:
                print(f"  Found {len(teams)} teams")
                for team in teams:
                    team['id'] = len(self.teams_db['teams'])
                    self.teams_db['teams'].append(team)
                    total_teams += 1
            
            # Be nice to the server
            time.sleep(0.3)
        
        print(f"\nKamigame: Added {total_teams} teams")
        return total_teams
    
    # ==================== GAMEWITH SCRAPER ====================
    
    def scrape_gamewith_team_pages(self):
        """Scrape key gamewith team composition guide pages."""
        print("\n" + "="*60)
        print("SCRAPING GAMEWITH")
        print("="*60)
        
        # Key gamewith pages with team compositions
        pages = [
            {'url': f'{self.gamewith_base}/article/show/165168', 'name': '火古戦場3500万編成', 'element': 'Fire'},
            {'url': f'{self.gamewith_base}/article/show/348298', 'name': '効率周回編成', 'element': 'Unknown'},
            {'url': f'{self.gamewith_base}/article/show/47075', 'name': '火マグナ編成', 'element': 'Fire'},
            {'url': f'{self.gamewith_base}/article/show/21595', 'name': 'アグニス編成', 'element': 'Fire'},
            # Water
            {'url': f'{self.gamewith_base}/article/show/47624', 'name': '水マグナ編成', 'element': 'Water'},
            {'url': f'{self.gamewith_base}/article/show/21811', 'name': 'ヴァルナ編成', 'element': 'Water'},
            # Earth
            {'url': f'{self.gamewith_base}/article/show/47435', 'name': '土マグナ編成', 'element': 'Earth'},
            {'url': f'{self.gamewith_base}/article/show/21607', 'name': 'ティターン編成', 'element': 'Earth'},
            # Wind
            {'url': f'{self.gamewith_base}/article/show/47483', 'name': '風マグナ編成', 'element': 'Wind'},
            {'url': f'{self.gamewith_base}/article/show/21676', 'name': 'ゼピュロス編成', 'element': 'Wind'},
            # Light
            {'url': f'{self.gamewith_base}/article/show/47452', 'name': '光マグナ編成', 'element': 'Light'},
            {'url': f'{self.gamewith_base}/article/show/21567', 'name': 'ゼウス編成', 'element': 'Light'},
            # Dark
            {'url': f'{self.gamewith_base}/article/show/47647', 'name': '闇マグナ編成', 'element': 'Dark'},
            {'url': f'{self.gamewith_base}/article/show/21551', 'name': 'ハデス編成', 'element': 'Dark'},
        ]
        
        total_teams = 0
        for page in pages:
            teams = self._scrape_gamewith_page(page['url'], page['name'], page['element'])
            if teams:
                print(f"  {page['name']}: {len(teams)} teams")
                for team in teams:
                    team['id'] = len(self.teams_db['teams'])
                    self.teams_db['teams'].append(team)
                    total_teams += 1
            time.sleep(1)
        
        print(f"\nGamewith: Added {total_teams} teams")
        return total_teams
    
    def _scrape_gamewith_page(self, url, page_name, page_element):
        """Scrape a single gamewith team guide page."""
        teams = []
        
        try:
            response = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find team composition sections
            # Gamewith typically uses h2/h3 for team names and divs for team data
            headers = soup.find_all(['h2', 'h3'])
            
            for header in headers:
                header_text = header.get_text(strip=True)
                
                # Look for team-related headers
                if any(skip in header_text for skip in ['目次', '関連', 'コメント', 'おすすめ', 'まとめ', '攻略', '報酬', '進め方']):
                    continue
                
                # Get the section content
                team_chars = []
                team_desc = []
                team_weapons = []
                team_summons = []
                
                current = header.find_next_sibling()
                depth = 0
                while current and current.name not in ['h2'] and depth < 30:
                    if current.name in ['div', 'p', 'table']:
                        text = current.get_text(strip=True)
                        if text and len(text) > 5:
                            team_desc.append(text[:400])
                        
                        # Try to extract character names from div text
                        # Gamewith uses dense text like: 主人公レリバルリア火ジークチチリ
                        if current.name == 'div' and len(text) > 10:
                            chars = self._extract_chars_from_gamewith_text(text, page_element)
                            for char in chars:
                                if char['name'] not in [c['name'] for c in team_chars]:
                                    team_chars.append(char)
                        
                        # Also check images
                        imgs = current.find_all('img', alt=True)
                        for img in imgs:
                            alt = img.get('alt', '').strip()
                            if alt and not any(skip in alt for skip in ['グラブル', '編成', '武器', '召喚石']):
                                resolved = self.resolve_japanese_name(alt, page_element)
                                if resolved and resolved['name'] not in [c['name'] for c in team_chars]:
                                    team_chars.append({
                                        'name': resolved['name'],
                                        'element': resolved.get('element', 'Unknown'),
                                        'role': 'Core'
                                    })
                    
                    current = current.find_next_sibling()
                    depth += 1
                
                # Only save if we found actual characters
                if len(team_chars) >= 2:
                    teams.append({
                        'team_name': f"{page_name} - {header_text}",
                        'element': page_element or 'Unknown',
                        'source': 'gamewith',
                        'source_url': url,
                        'characters': team_chars,
                        'description': ' '.join(team_desc[:2])[:300] if team_desc else ''
                    })
            
            return teams
            
        except Exception as e:
            print(f"  Error scraping gamewith {url}: {e}")
            return []
    
    def _extract_chars_from_gamewith_text(self, text, page_element):
        """Extract character names from gamewith's dense text format."""
        chars = []
        
        # Only process divs that look like team composition divs
        # Gamewith team divs typically contain patterns like:
        # "主人公レリバルリア火ジークチチリメイン召喚サポ召喚"
        # They mention 主人公 (main character), メイン召喚 (main summon), etc.
        if not any(marker in text for marker in ['主人公', 'メイン召喚', 'サポ召喚', 'メイン武器', '覚醒']):
            return chars
        
        # Extract character names by looking for known names in the text
        # Sort by length descending to match longer names first (prevents partial matches)
        sorted_names = sorted(self.jpname_map.items(), key=lambda x: -len(x[0]))
        
        for jp_name, candidates in sorted_names:
            if len(jp_name) < 2:
                continue
            # Check if this name appears in the text
            pattern = re.escape(jp_name)
            if re.search(pattern, text):
                # Disambiguate
                if len(candidates) == 1:
                    char = candidates[0]
                    if char['name'] not in [c['name'] for c in chars]:
                        chars.append({
                            'name': char['name'],
                            'element': char.get('element', 'Unknown'),
                            'role': 'Core'
                        })
                else:
                    # Try to pick based on page element
                    for c in candidates:
                        if c.get('element') == page_element:
                            if c['name'] not in [ch['name'] for ch in chars]:
                                chars.append({
                                    'name': c['name'],
                                    'element': c.get('element', 'Unknown'),
                                    'role': 'Core'
                                })
                            break
                    else:
                        if candidates[0]['name'] not in [c['name'] for c in chars]:
                            chars.append({
                                'name': candidates[0]['name'],
                                'element': candidates[0].get('element', 'Unknown'),
                                'role': 'Core'
                            })
        
        # Also check transformed names
        for short_name, full_name in self.name_transforms.items():
            if short_name in text and full_name in self.jpname_map:
                candidates = self.jpname_map[full_name]
                for c in candidates:
                    if c.get('element') == page_element:
                        if not any(ch['name'] == c['name'] for ch in chars):
                            chars.append({
                                'name': c['name'],
                                'element': c.get('element', 'Unknown'),
                                'role': 'Core'
                            })
                        break
        
        return chars
    
    # ==================== DATABASE MANAGEMENT ====================
    
    def load_existing_database(self, filename='teams_database.json'):
        """Load existing teams database."""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                
                # Keep manual entries, remove old scraped ones
                keep_teams = []
                for team in existing.get('teams', []):
                    source = team.get('source', 'manual')
                    if source == 'manual':
                        keep_teams.append(team)

                self.teams_db['teams'] = keep_teams
                print(f"Loaded {len(keep_teams)} existing manual teams")
                return True
            except Exception as e:
                print(f"Error loading database: {e}")
        return False
    
    def save_database(self, filename=None):
        """Save teams database to JSON."""
        if filename is None:
            filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'teams_database.json')
        
        self.teams_db['last_updated'] = datetime.now().isoformat()
        
        # Reassign IDs sequentially
        for i, team in enumerate(self.teams_db['teams']):
            team['id'] = i
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.teams_db, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Database saved to {filename}")
        print(f"Total teams: {len(self.teams_db['teams'])}")
        print(f"{'='*60}")
    
    def generate_summary(self):
        """Generate a summary of the database."""
        teams = self.teams_db['teams']
        
        print("\n" + "="*60)
        print("DATABASE SUMMARY")
        print("="*60)
        
        by_element = {}
        by_source = {}
        char_count = {}
        
        for team in teams:
            elem = team.get('element', 'Unknown')
            by_element[elem] = by_element.get(elem, 0) + 1
            
            src = team.get('source', 'unknown')
            by_source[src] = by_source.get(src, 0) + 1
            
            for char in team.get('characters', []):
                name = char.get('name', 'Unknown')
                char_count[name] = char_count.get(name, 0) + 1
        
        print(f"\nTotal teams: {len(teams)}")
        
        print("\nBy Element:")
        for elem, count in sorted(by_element.items(), key=lambda x: -x[1]):
            print(f"  {elem}: {count}")
        
        print("\nBy Source:")
        for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
            print(f"  {src}: {count}")
        
        print("\nTop 20 Characters in Teams:")
        for name, count in sorted(char_count.items(), key=lambda x: -x[1])[:20]:
            print(f"  {name}: {count}")


def main():
    scraper = GBFTeamScraper()
    
    # Load existing database (keeps manual teams)
    scraper.load_existing_database()
    
    # Fetch wiki character database for name mapping
    scraper.fetch_wiki_database()
    
    # Scrape kamigame (all characters)
    print("\nScraping kamigame character pages...")
    kamigame_teams = scraper.scrape_kamigame_all(max_chars=None)
    
    # Scrape gamewith key team pages
    gamewith_teams = scraper.scrape_gamewith_team_pages()
    
    # Generate summary
    scraper.generate_summary()
    
    # Save
    scraper.save_database()
    
    print("\nDone! Run 'python3 planner.py' to see team recommendations.")


if __name__ == "__main__":
    main()
