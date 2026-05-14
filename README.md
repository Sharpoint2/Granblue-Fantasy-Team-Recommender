# GBF Team Planner

A tool for Granblue Fantasy players to track their character collection and get team recommendations based on their roster.

## Features

- **Collection Tracking**: Import your gbf.wiki Collection Tracker URL to see which characters you own
- **Team Recommendations**: Get personalized team suggestions based on your collection
- **Teams Database**: Store and manage team compositions from various sources (Kamigame, Gamewith, community)
- **Element-Specific Matching**: Correctly handles characters with multiple versions (e.g., Fire Zeta vs Water Zeta)

## Quick Start

### 1. Get Your Collection Tracker URL

1. Go to https://gbf.wiki/Collection_Tracker
2. Click on characters you own to mark them
3. Export the URL:
   - Press F12 to open Developer Tools
   - Click Console tab
   - Type: `copy(location.href)` and press Enter
   - The URL is now copied to your clipboard

### 2. Save Your Tracker URL

Create a file named `tracker_url.txt` in the gbf-planner folder and paste your URL there.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Planner

```bash
python3 planner.py
```

Then press Enter to use your saved tracker URL.

## Team Database

### View Teams

```bash
# List all teams
python3 team_database.py list

# List teams for a specific element
python3 team_database.py list Water

# Show team details
python3 team_database.py show 0

# Find teams with a specific character
python3 team_database.py find Zeta
```

### Add a Team

```bash
python3 team_database.py add
```

This will start an interactive prompt to add a new team composition.

## Scraping Teams

To build or update the team database from Kamigame and Gamewith:

```bash
python3 scrapers/scrape_kamigame_gamewith.py
```

This will:
1. Fetch all characters from gbf.wiki for name mapping
2. Scrape ~1000 character pages from Kamigame for team examples
3. Scrape element-specific team guides from Gamewith
4. Merge with existing manual entries
5. Save to `data/teams_database.json`

The scraper maps Japanese character names to English using gbf.wiki's `jpname` field.

## Project Structure

```
gbf-planner/
├── planner.py                 # Main entry point
├── team_database.py           # CLI for team database
├── tracker_url.txt            # Your tracker URL (create this)
├── requirements.txt           # Python dependencies
├── gbfplanner/                # Core package
│   ├── decoder.py             # Tracker URL decoding
│   ├── wiki.py                # GBF Wiki Cargo API
│   ├── matcher.py             # Character matching logic
│   └── database.py            # Team database operations
├── scrapers/                  # Scraping scripts
│   └── scrape_kamigame_gamewith.py  # Kamigame + Gamewith scraper
├── data/                      # Data files
│   ├── teams_database.json    # Team compositions database
│   ├── tracker_id_list.py     # Hardcoded tracker ID list
│   └── jpname_mapping.json    # Japanese name mappings
└── utils/                     # Utility scripts
    ├── check_tracker.py       # Verify tracker URL decoding
    ├── show_missing.py        # Show unmapped tracker bits
    └── save_tracker_url.py    # Save tracker URL helper
```

## Troubleshooting

### "41 characters could not be decoded"

This is normal! The hash has room for 1944 indices but the tracker only has 1405 characters. The extra space is for future characters. Your decoded characters should still be accurate.

### URL Truncation

If your terminal truncates long URLs, use the file input method:
1. Save your full URL to `tracker_url.txt`
2. Run `python3 planner.py` and press Enter

## Data Sources

- **Character Data**: GBF Wiki Cargo API (https://gbf.wiki/)
- **Team Compositions**: Kamigame, Gamewith, Community contributions

## License

MIT License - Feel free to modify and distribute.
