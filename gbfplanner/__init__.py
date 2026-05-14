"""
GBF Planner core package.

Modules:
    decoder: gbf.wiki tracker URL decoding
    wiki: GBF Wiki Cargo API interactions
    matcher: Character matching and lookup logic
    database: Team database operations
"""

from .decoder import decode_tracker_url, get_tracker_id_list, clear_tracker_cache
from .wiki import fetch_wiki_character_db
from .matcher import (
    build_lookup,
    matches_character_spec,
    get_character_display_name,
    generate_team_recommendations,
    get_owned_flex_options,
)
from .database import TeamDatabase, DATABASE_FILE

__all__ = [
    "decode_tracker_url",
    "get_tracker_id_list",
    "clear_tracker_cache",
    "fetch_wiki_character_db",
    "build_lookup",
    "matches_character_spec",
    "get_character_display_name",
    "generate_team_recommendations",
    "get_owned_flex_options",
    "TeamDatabase",
    "DATABASE_FILE",
]
