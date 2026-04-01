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

# Initialize database
python db.py
```

### Running the Application

```bash
# Start the FastAPI server
uvicorn main:app --reload
```

Visit `http://localhost:8000` to access the web interface.

## Data Sources

- OHL Historical Stats (2000-2025)
- Erie Otters Official Records
- Game Statistics Archives

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
