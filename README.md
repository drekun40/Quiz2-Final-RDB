# Erie Otters OHL Database Project

A relational database project tracking Erie Otters (Ontario Hockey League) team statistics and performance from 2000-2025.

## Project Overview

This project builds a SQLite database containing:
- **Teams**: Erie Otters and opponent information
- **Players**: Roster data across seasons (2000-2025)
- **Games**: Game-by-game statistics and results
- **Stats**: Individual player and team performance metrics
- **Seasons**: Annual season summaries and achievements

## Features

- SQLite relational database with normalized schema
- Python data pipeline for CSV ingestion
- FastAPI web interface for querying
- Statistical analysis and visualizations
- Machine learning predictions (game outcomes, player performance)

## Project Structure

```
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── models.py                      # SQLModel database schemas
├── db.py                          # Database initialization & utilities
├── db_optimized.py                # Optimized database operations
├── main.py                        # FastAPI web application
├── train.py                       # ML model training
├── predict.py                     # ML predictions
├── data/                          # Data files
│   ├── erie_otters_stats.csv
│   ├── games_data.csv
│   └── player_stats.csv
├── static/                        # Web UI assets
│   ├── index.html
│   └── style.css
└── models/                        # Saved ML models
    └── predictions.pth
```

## Getting Started

### Prerequisites
- Python 3.8+
- SQLite3
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/drekun40/Quiz2-Final-RDB.git
cd Quiz2-Final-RDB

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize and populate database
python load_data.py
```

### Running the Application

#### Option 1: Using the start script
```bash
python server.py
```

#### Option 2: Direct uvicorn
```bash
uvicorn main:app --reload --host localhost --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

#### Test the API

```bash
# Get all players
curl http://localhost:8000/players

# Get top scorers for 2025
curl http://localhost:8000/stats/top-scorers/2025

# Get team statistics
curl http://localhost:8000/stats/team-record/2025
```

## Data Sources

The project includes a multi-season scraper that can extract data from all 25 seasons (2000-2025):

### Using the Scraper

The scraper is configured to scrape from these URLs:
- Season 1-25: `https://chl.ca/ohl-otters/stats/players/{season_number}/`
- Maps to years 2000-2026

**Run the scraper:**
```bash
python scraper.py
```

This will:
- Scrape specified seasons (currently testing seasons 24-26)
- Save data to `data/erie_otters_all_seasons.csv`
- Save JSON backup to `data/erie_otters_all_seasons.json`

**To scrape all 25 seasons**, modify `scraper.py`:
```python
# Change this line in __main__:
test_seasons = [26, 25, 24]  # Current: recent seasons only

# To this:
test_seasons = list(range(1, 27))  # All 26 seasons (2000-2026)
```

**Note:** The website may enforce rate limiting. If blocked, requests will return 403.

### Current Data (2025-2026)

- Real Erie Otters roster with 30 players
- Complete season statistics
- Player stats: games played, goals, assists, points, +/-, PIM
- Team stats: wins, losses, OT losses, goals for/against, power play %

## Database Schema

### Teams
- team_id (PK)
- name
- founded_year
- city
- league

### Players
- player_id (PK)
- first_name
- last_name
- birth_year
- position
- draft_year

### Games
- game_id (PK)
- season
- game_date
- home_team
- away_team
- home_score
- away_score

### PlayerStats
- stat_id (PK)
- player_id (FK)
- season
- games_played
- goals
- assists
- points
- +/-

### TeamStats
- stat_id (PK)
- team_id (FK)
- season
- wins
- losses
- ot_losses
- goals_for
- goals_against

## License

Your Name (Year)

## Author

Created as a Final Project in Relational Database Course
