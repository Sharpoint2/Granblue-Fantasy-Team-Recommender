#!/usr/bin/env python3
"""
Team database CLI - wrapper around gbfplanner.database.

Usage:
    python3 team_database.py list [element]
    python3 team_database.py add
    python3 team_database.py show <team_id>
    python3 team_database.py find <character>
    python3 team_database.py remove <team_id>
"""

import sys

from gbfplanner.database import TeamDatabase, interactive_add_team


def main():
    db = TeamDatabase()
    
    if len(sys.argv) < 2:
        print("Usage: python3 team_database.py <command> [args]")
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
