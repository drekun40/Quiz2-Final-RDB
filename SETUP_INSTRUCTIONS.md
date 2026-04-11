# 🏒 Erie Otters Stats Dashboard - Setup Instructions

## Quick Start (For First-Time Users)

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/drekun40/Quiz2-Final-RDB.git
   cd Quiz2-Final-RDB
   ```

2. **Create a Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   python server.py
   ```

5. **Open in browser:**
   - Navigate to `http://localhost:8000`
   - Data will be automatically loaded from the included databases

## ✅ What's Included

The repository includes **pre-populated databases** with complete player data for all 10 seasons (2010-2019):

- **Erie Otters 2010-2019 Data**: 172 unique player records across 10 seasons
- **10 SQLite Databases**: One per season (eredmond_otters_2010.db through 2019.db)
- **No setup scripts required** - databases are ready to use immediately

## 🌐 Available Features

### Pages:
- **Home** (`/`) - Overview dashboard
- **Players** (`/players`) - Browsable player roster by season
- **Leaders** (`/leaders`) - Top performers leaderboard
- **Projections** (`/predict`) - Season analysis dashboard with charts
- **Data Info** (`/about-data`) - Data sources and documentation

### Season Options:
- Individual seasons (2010-2019)
- **All Seasons** - Career statistics across all 10 seasons

### Dashboard Features:
- 4 interactive charts (Top Scorers, PPG Leaders, Goals vs Assists, Games Played)
- Player search and position filtering
- Season-by-season and career statistics
- SQL queries displayed for learning purposes

## 📊 Database Structure

Each season database contains:
- **Players**: Player IDs, names, positions, jersey numbers
- **Player Stats**: Goals, assists, points, games played, penalty minutes per season
- **Teams**: Team information
- **Refresh Logs**: Data update tracking

## 🔄 Troubleshooting

**No data showing on startup:**
- Verify all `erie_otters_*.db` files are in the project root
- Check that Python virtual environment is activated
- Run `python server.py` to see startup errors

**Port 8000 already in use:**
```bash
# Kill existing processes
pkill -f "python server.py"
# Or on macOS: lsof -i :8000 and kill the PID
```

**ImportError with dependencies:**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## 📝 Project Structure

```
Quiz2-Final-RDB/
├── README.md                    # Project documentation
├── SETUP_INSTRUCTIONS.md        # This file
├── requirements.txt             # Python dependencies
├── server.py                    # Main server entry point
│
├── app/
│   ├── main.py                 # FastAPI application setup
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLModel schemas
│   ├── schemas.py              # Pydantic schemas
│   │
│   ├── routers/
│   │   ├── pages.py            # Web page routes
│   │   └── debug.py            # Debug/audit routes
│   │
│   ├── services/
│   │   ├── deduplication.py    # Duplicate handling
│   │   ├── database_cleanup.py # Cleanup utilities
│   │   ├── analysis_service.py # Statistical analysis
│   │   ├── stats_service.py    # Stats calculations
│   │   └── predictor.py        # Prediction models
│   │
│   ├── templates/
│   │   ├── base.html           # Base template
│   │   ├── index.html          # Homepage
│   │   ├── players.html        # Players page
│   │   ├── leaders.html        # Leaderboards
│   │   ├── predict.html        # Dashboard with charts
│   │   └── about_data.html     # Data information
│   │
│   └── static/
│       └── styles.css          # Styling
│
├── erie_otters_2010.db         # Season 2010-2011 data
├── erie_otters_2011.db         # Season 2011-2012 data
│   ... (through 2019)
├── erie_otters_2019.db         # Season 2019-2020 data
│
└── .venv/                       # Virtual environment (created locally)
```

## 🛠️ Development Commands

### Run the server with debug output:
```bash
python server.py 2>&1 | tee server.log
```

### View database audit/health:
```
http://localhost:8000/debug/summary
```

### Test a specific season:
```
http://localhost:8000/predict?season=2019
http://localhost:8000/predict?season=all
```

## 📌 Key Information

- **Database Type**: SQLite (local files, no external server needed)
- **Framework**: FastAPI
- **ORM**: SQLModel
- **Default Season**: 2019 (most recent)
- **Player Count by Season**: 15-20 unique players per season

## ✨ What Makes This Different

1. **Pre-populated data** - No scraping or setup required
2. **Deduplication** - Database clean with 0 duplicates
3. **Cross-season support** - View individual seasons or 10-year career stats
4. **Interactive charts** - Real-time visualization of player statistics
5. **Educational** - SQL queries displayed on every page for learning

---

**Questions?** Check the GitHub issues or review the database structure in `app/models.py`
