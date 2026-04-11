# 🏒 Erie Otters Statistics Dashboard

A modern, interactive web application for exploring Erie Otters (Ontario Hockey League) player statistics across 10 seasons (2010-2019).

## ✨ Features

- **🎯 Interactive Dashboard** - Real-time charts and statistics
- **📊 4 Auto-Updating Charts** - Points, PPG, Goals vs Assists, Games Played
- **📅 Multi-Season Support** - View individual seasons or career stats across all 10 years
- **🔍 Player Search & Filtering** - Find players by name or position
- **📈 Career Analysis** - Track player development across seasons
- **💾 Pre-Populated Data** - 172 unique player records ready to go
- **🎓 Educational** - SQL queries visible on every page

## 🚀 Quick Start

See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for detailed setup steps.

**TL;DR:**
```bash
git clone https://github.com/drekun40/Quiz2-Final-RDB.git
cd Quiz2-Final-RDB
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python server.py
# Open http://localhost:8000
```

## 📱 Available Pages

| Page | URL | Description |
|------|-----|-------------|
| **Home** | `/` | Season overview and quick stats |
| **Players** | `/players` | Browsable roster with search |
| **Leaders** | `/leaders` | Top scorers and performers |
| **Projections** | `/predict` | Season dashboard with charts |
| **Data Info** | `/about-data` | Data sources and tracking |

## 🗂️ Database Contents

✅ **All 10 Seasons Included (2010-2019)**
- Season 2010: 15 players
- Season 2011: 15 players
- Season 2012: 16 players
- ...
- Season 2019: 20 players
- **Total: 172 unique player records with 0 duplicates**

Each season database includes:
- Player rosters
- Goals, assists, points
- Games played
- Penalty minutes
- PPG (Points Per Game)

## 🛠️ Technology Stack

- **Backend**: FastAPI + SQLModel
- **Frontend**: Jinja2 templates + Chart.js
- **Database**: SQLite (local, no external server)
- **Language**: Python 3.8+

## 📊 Dashboard Features

### Charts Available
1. **Top 10 Scorers - Points Comparison** - Horizontal bar chart
2. **Points Per Game Leaders** - PPG rankings
3. **Top Scorers - Goals vs Assists** - Stacked comparison
4. **Games Played Distribution** - Game frequency analysis

### Season Options
- Individual years (2010-2019)
- **All Seasons** - Aggregate career statistics
- Automatic averages and totals calculation

## 🔧 Requirements

- Python 3.8+
- pip package manager
- ~50MB disk space (databases included)

## 📋 Project Structure

```
├── app/                          # FastAPI application
│   ├── main.py                  # Server setup
│   ├── database.py              # Database config
│   ├── models.py                # SQLModel schemas
│   ├── routers/                 # URL route handlers
│   ├── services/                # Business logic
│   ├── templates/               # HTML templates
│   └── static/                  # CSS and assets
├── erie_otters_2010.db          # Season databases (included)
├── erie_otters_2011.db
│   ... (through 2019)
├── server.py                    # Application entry point
└── requirements.txt             # Python dependencies
```

## 💡 Key Updates

### Version 2.0 (Latest)
- ✅ Fixed chart rendering (4 interactive charts)
- ✅ Added "All Seasons" aggregation
- ✅ Databases now included (no setup needed)
- ✅ Clean, deduped data (0 duplicates)
- ✅ Cross-season career stats
- ✅ Responsive design

## 🐛 Troubleshooting

**No data visible?**
- Ensure all `erie_otters_*.db` files are in the project root
- Check Python virtual environment is activated
- Try: `python server.py` to see startup messages

**Port 8000 in use?**
```bash
pkill -f "python server.py"
```

## 📞 Support

1. Check [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
2. Review database structure in `app/models.py`
3. Check GitHub issues for known problems

---

**Ready to get started?** → [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
