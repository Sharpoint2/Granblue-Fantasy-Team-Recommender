"""Character matching and lookup logic for GBF Planner."""


def build_lookup(wiki_db):
    """Build lookup structures for character matching.
    
    Returns:
        name_to_ids: Mapping from name to list of all IDs with that name
        id_to_char: Mapping from ID to character data
        name_element_to_ids: Mapping from (name, element) to list of IDs
    """
    name_to_ids = {}
    id_to_char = {}
    name_element_to_ids = {}
    
    for char_id, char in wiki_db.items():
        name = char['name']
        element = char['element']
        
        id_to_char[char_id] = char
        
        if name not in name_to_ids:
            name_to_ids[name] = []
        name_to_ids[name].append(char_id)
        
        key = (name, element)
        if key not in name_element_to_ids:
            name_element_to_ids[key] = []
        name_element_to_ids[key].append(char_id)
    
    return name_to_ids, id_to_char, name_element_to_ids


def matches_character_spec(spec, owned_ids, wiki_db, name_to_ids, name_element_to_ids):
    """Check if any owned character matches the character specification.
    
    Args:
        spec: Character specification - can be:
            - ID string (exact match)
            - Dict with 'name' and optionally 'element'
            - Name string (matches any version)
        owned_ids: Set of owned character IDs
        wiki_db: Character database
        name_to_ids: Name -> IDs mapping
        name_element_to_ids: (name, element) -> IDs mapping
    
    Returns:
        True if user owns a matching character
    """
    # Case 1: Direct ID match
    if isinstance(spec, str) and spec in owned_ids:
        return True
    
    # Case 2: Dict specification with name and optional element
    if isinstance(spec, dict):
        name = spec.get('name')
        element = spec.get('element')
        
        if element:
            # Match specific name + element
            key = (name, element)
            if key in name_element_to_ids:
                return any(char_id in owned_ids for char_id in name_element_to_ids[key])
        else:
            # Match any version of this name
            if name in name_to_ids:
                return any(char_id in owned_ids for char_id in name_to_ids[name])
        return False
    
    # Case 3: Just a name string (matches any version)
    if isinstance(spec, str):
        if spec in name_to_ids:
            return any(char_id in owned_ids for char_id in name_to_ids[spec])
    
    return False


def get_character_display_name(spec):
    """Get a display name for a character specification."""
    if isinstance(spec, dict):
        name = spec.get('name', 'Unknown')
        element = spec.get('element')
        if element:
            return f"{name} ({element})"
        return name
    if isinstance(spec, str):
        return spec
    return str(spec)


def generate_team_recommendations(owned_ids, meta_teams, wiki_db):
    """Finds teams where the user owns all the required core characters.
    
    Args:
        owned_ids: Set of owned character IDs
        meta_teams: List of team dictionaries with character specs
        wiki_db: Character database with ID as key
    """
    print("Cross-referencing roster with meta teams...\n")
    
    name_to_ids, id_to_char, name_element_to_ids = build_lookup(wiki_db)
    buildable_teams = []
    
    for team in meta_teams:
        # Check if user owns the required version of each core character
        all_core_owned = True
        
        for spec in team["core_characters"]:
            if not matches_character_spec(spec, owned_ids, wiki_db, name_to_ids, name_element_to_ids):
                all_core_owned = False
                break
        
        if all_core_owned:
            buildable_teams.append(team)
            
    return buildable_teams


def get_owned_flex_options(team, owned_ids, wiki_db):
    """Get the flex options the user owns for a team."""
    name_to_ids, id_to_char, name_element_to_ids = build_lookup(wiki_db)
    owned_flex = []
    for spec in team['flex_options']:
        if matches_character_spec(spec, owned_ids, wiki_db, name_to_ids, name_element_to_ids):
            owned_flex.append(get_character_display_name(spec))
    return owned_flex
