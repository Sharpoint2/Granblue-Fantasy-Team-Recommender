"""Team database operations for GBF Planner."""

import json
import os
from datetime import datetime

# Default database path, relative to project root
DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'teams_database.json')


class TeamDatabase:
    def __init__(self, db_file=None):
        self.db_file = db_file or DATABASE_FILE
        self.data = {
            "version": "1.1",
            "last_updated": "",
            "teams": [],
            "characters": {},
            "sources": {
                "kamigame": "https://kamigame.jp/granbluefantasy/",
                "gamewith": "https://gamewith.jp/granbluefantasy/"
            }
        }
        self.load()
    
    def load(self):
        """Load database from file."""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.data.update(loaded)
            print(f"Loaded {len(self.data['teams'])} teams from database")
        else:
            print("Creating new team database")
    
    def save(self):
        """Save database to file."""
        self.data['last_updated'] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"Database saved ({len(self.data['teams'])} teams)")
    
    def add_team(self, team_data):
        """Add a new team to the database."""
        required = ['team_name', 'element', 'characters']
        for field in required:
            if field not in team_data:
                print(f"Error: Missing required field '{field}'")
                return False
        
        team_data['added_date'] = datetime.now().isoformat()
        team_data['id'] = len(self.data['teams'])
        
        self.data['teams'].append(team_data)
        print(f"Added team: {team_data['team_name']}")
        return True
    
    def remove_team(self, team_id):
        """Remove a team by ID."""
        for i, team in enumerate(self.data['teams']):
            if team.get('id') == team_id:
                del self.data['teams'][i]
                print(f"Removed team ID {team_id}")
                return True
        print(f"Team ID {team_id} not found")
        return False
    
    def find_teams_by_character(self, char_name, element=None):
        """Find all teams that include a specific character."""
        results = []
        for team in self.data['teams']:
            for char in team.get('characters', []):
                if char.get('name') == char_name:
                    if element is None or char.get('element') == element:
                        results.append(team)
                        break
        return results
    
    def find_teams_by_element(self, element):
        """Find all teams for a specific element."""
        return [t for t in self.data['teams'] if t.get('element') == element]
    
    def list_teams(self, element=None, limit=20):
        """List teams with optional filtering."""
        teams = self.data['teams']
        
        if element:
            teams = [t for t in teams if t.get('element') == element]
        
        print(f"\nShowing {min(limit, len(teams))} of {len(teams)} teams:")
        print("-" * 60)
        
        for i, team in enumerate(teams[:limit]):
            chars = ', '.join([c.get('name', '?') for c in team.get('characters', [])[:3]])
            print(f"{i+1}. {team['team_name']} ({team['element']})")
            print(f"   Core: {chars}")
            if team.get('description'):
                print(f"   {team['description'][:80]}...")
            print()
    
    def get_team_details(self, team_id):
        """Get detailed information about a team."""
        for team in self.data['teams']:
            if team.get('id') == team_id:
                return team
        return None
    
    def print_team_details(self, team_id):
        """Print detailed team information."""
        team = self.get_team_details(team_id)
        if not team:
            print(f"Team ID {team_id} not found")
            return
        
        print(f"\n{'='*60}")
        print(f"Team: {team['team_name']}")
        print(f"Element: {team['element']}")
        print(f"{'='*60}\n")
        
        if team.get('description'):
            print(f"Description: {team['description']}\n")
        
        print("Core Characters:")
        for char in team.get('characters', []):
            req = " (REQUIRED)" if char.get('required') else ""
            print(f"  - {char['name']} ({char.get('element', '?')}) - {char.get('role', 'Unknown')}{req}")
        
        if team.get('flex_slots'):
            print("\nFlex Options:")
            for char in team.get('flex_slots', []):
                print(f"  - {char['name']} ({char.get('element', '?')}) - {char.get('role', 'Unknown')}")
        
        if team.get('weapons'):
            print(f"\nRecommended Weapons: {', '.join(team['weapons'])}")
        
        if team.get('summons'):
            print(f"Recommended Summons: {', '.join(team['summons'])}")
        
        if team.get('content_types'):
            print(f"Content Types: {', '.join(team['content_types'])}")
        
        if team.get('source_url'):
            print(f"\nSource: {team['source_url']}")


def interactive_add_team(db_file=None):
    """Interactive prompt to add a team."""
    db = TeamDatabase(db_file=db_file)
    
    print("\n=== Add New Team ===\n")
    
    team = {}
    team['team_name'] = input("Team name: ").strip()
    team['element'] = input("Element (Fire/Water/Earth/Wind/Light/Dark): ").strip()
    team['description'] = input("Description: ").strip()
    
    # Core characters
    print("\nEnter core characters (required for the team):")
    team['characters'] = []
    while True:
        name = input("  Character name (or press Enter to finish): ").strip()
        if not name:
            break
        element = input(f"    Element for {name}: ").strip()
        role = input(f"    Role for {name} (e.g., DPS, Support, Tank): ").strip()
        team['characters'].append({
            'name': name,
            'element': element,
            'role': role,
            'required': True
        })
    
    # Flex slots
    print("\nEnter flex/replacement characters (optional):")
    team['flex_slots'] = []
    while True:
        name = input("  Character name (or press Enter to finish): ").strip()
        if not name:
            break
        element = input(f"    Element for {name}: ").strip()
        role = input(f"    Role for {name}: ").strip()
        team['flex_slots'].append({
            'name': name,
            'element': element,
            'role': role
        })
    
    # Additional info
    weapons = input("\nRecommended weapons (comma-separated, or press Enter to skip): ").strip()
    if weapons:
        team['weapons'] = [w.strip() for w in weapons.split(',')]
    
    summons = input("Recommended summons (comma-separated, or press Enter to skip): ").strip()
    if summons:
        team['summons'] = [s.strip() for s in summons.split(',')]
    
    content = input("Content types (e.g., Guild Wars, High Difficulty): ").strip()
    if content:
        team['content_types'] = [c.strip() for c in content.split(',')]
    
    # Add to database
    if db.add_team(team):
        db.save()
        print(f"\n✓ Team '{team['team_name']}' added successfully!")
    else:
        print("\n✗ Failed to add team")


def main():
    """Main command-line interface."""
    import sys
    
    db = TeamDatabase()
    
    if len(sys.argv) < 2:
        print("Usage: python3 -m team_database <command> [args]")
        print("\nCommands:")
        print("  list [element]        - List all teams (optionally filter by element)")
        print("  add                   - Add a new team interactively")
        print("  show <team_id>        - Show detailed team information")
        print("  find <character>      - Find teams containing a character")
        print("  remove <team_id>      - Remove a team by ID")
        print("  import <file.json>    - Import teams from JSON file")
        print("\nExamples:")
        print("  python3 team_database.py list Water")
        print("  python3 team_database.py find Zeta")
        print("  python3 team_database.py show 0")
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        element = sys.argv[2] if len(sys.argv) > 2 else None
        db.list_teams(element)
    
    elif command == 'add':
        interactive_add_team()
    
    elif command == 'show':
        if len(sys.argv) < 3:
            print("Error: Please provide a team ID")
            return
        db.print_team_details(int(sys.argv[2]))
    
    elif command == 'find':
        if len(sys.argv) < 3:
            print("Error: Please provide a character name")
            return
        char_name = sys.argv[2]
        element = sys.argv[3] if len(sys.argv) > 3 else None
        
        teams = db.find_teams_by_character(char_name, element)
        print(f"\nFound {len(teams)} teams with {char_name}:")
        for team in teams:
            print(f"  - {team['team_name']} ({team['element']})")
    
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("Error: Please provide a team ID")
            return
        db.remove_team(int(sys.argv[2]))
        db.save()
    
    elif command == 'import':
        if len(sys.argv) < 3:
            print("Error: Please provide a JSON file path")
            return
        print("Import feature not yet implemented")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
