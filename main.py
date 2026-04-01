from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from models import engine, create_db_and_tables, Team, Player, Game, PlayerStats, TeamStats, Season, get_session
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path


# Initialize FastAPI app
app = FastAPI(title="Erie Otters OHL Database API", version="1.0.0")

# Create tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# Mount static files
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================================================
# Response Models
# ============================================================================

class TeamResponse(BaseModel):
    team_id: int
    name: str
    city: str
    founded_year: int
    league: str


class PlayerResponse(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    birth_year: int
    position: str


class GameResponse(BaseModel):
    game_id: int
    season: int
    game_date: str
    home_team_id: int
    away_team_id: int
    home_score: int
    away_score: int


class PlayerStatsResponse(BaseModel):
    stat_id: int
    player_id: int
    season: int
    games_played: int
    goals: int
    assists: int
    points: int


# ============================================================================
# Team Endpoints
# ============================================================================

@app.get("/teams")
def get_teams():
    """Get all teams"""
    with Session(engine) as session:
        teams = session.exec(select(Team)).all()
        return [{"team_id": t.team_id, "name": t.name, "city": t.city, 
                "founded_year": t.founded_year, "league": t.league} for t in teams]


@app.get("/teams/{team_id}", response_model=TeamResponse)
def get_team(team_id: int):
    """Get a specific team by ID"""
    with Session(engine) as session:
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team


@app.post("/teams", response_model=TeamResponse)
def create_team(team: Team):
    """Create a new team"""
    with Session(engine) as session:
        session.add(team)
        session.commit()
        session.refresh(team)
        return team


# ============================================================================
# Player Endpoints
# ============================================================================

@app.get("/players")
def get_players(position: Optional[str] = None):
    """Get all players, optionally filtered by position"""
    with Session(engine) as session:
        query = select(Player)
        if position:
            query = query.where(Player.position == position)
        players = session.exec(query).all()
        return [{"player_id": p.player_id, "first_name": p.first_name, "last_name": p.last_name, 
                "birth_year": p.birth_year, "position": p.position, "draft_year": p.draft_year} for p in players]


@app.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: int):
    """Get a specific player by ID"""
    with Session(engine) as session:
        player = session.get(Player, player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return player


@app.post("/players", response_model=PlayerResponse)
def create_player(player: Player):
    """Create a new player"""
    with Session(engine) as session:
        session.add(player)
        session.commit()
        session.refresh(player)
        return player


# ============================================================================
# Game Endpoints
# ============================================================================

@app.get("/games")
def get_games(season: Optional[int] = None):
    """Get all games, optionally filtered by season"""
    with Session(engine) as session:
        query = select(Game)
        if season:
            query = query.where(Game.season == season)
        games = session.exec(query).all()
        return [{"game_id": g.game_id, "season": g.season, "game_date": str(g.game_date),
                "home_team_id": g.home_team_id, "away_team_id": g.away_team_id,
                "home_score": g.home_score, "away_score": g.away_score} for g in games]


@app.get("/games/{game_id}", response_model=GameResponse)
def get_game(game_id: int):
    """Get a specific game by ID"""
    with Session(engine) as session:
        game = session.get(Game, game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game


# ============================================================================
# Player Stats Endpoints
# ============================================================================

@app.get("/player-stats")
def get_player_stats(player_id: Optional[int] = None, season: Optional[int] = None):
    """Get player stats, optionally filtered by player_id or season"""
    with Session(engine) as session:
        query = select(PlayerStats)
        if player_id:
            query = query.where(PlayerStats.player_id == player_id)
        if season:
            query = query.where(PlayerStats.season == season)
        stats = session.exec(query).all()
        return [{"stat_id": s.stat_id, "player_id": s.player_id, "season": s.season,
                "games_played": s.games_played, "goals": s.goals, "assists": s.assists,
                "points": s.points, "plus_minus": s.plus_minus, "penalty_minutes": s.penalty_minutes} for s in stats]


# ============================================================================
# Statistics Endpoints
# ============================================================================

@app.get("/stats/top-scorers/{season}")
def get_top_scorers(season: int, limit: int = 10):
    """Get top goal scorers for a season"""
    with Session(engine) as session:
        query = (
            select(Player, PlayerStats)
            .join(PlayerStats)
            .where(PlayerStats.season == season)
            .order_by(PlayerStats.goals.desc())
            .limit(limit)
        )
        results = session.exec(query).all()
        return [
            {
                "player": result[0],
                "stats": result[1]
            }
            for result in results
        ]


@app.get("/stats/team-record/{season}")
def get_team_record(season: int):
    """Get team records for a season"""
    with Session(engine) as session:
        stats = session.exec(
            select(Team, TeamStats)
            .join(TeamStats)
            .where(TeamStats.season == season)
        ).all()
        return [
            {
                "team": result[0],
                "stats": result[1]
            }
            for result in stats
        ]


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
def read_root():
    """API documentation"""
    return {
        "message": "Erie Otters OHL Database API",
        "version": "1.0.0",
        "endpoints": {
            "teams": "/teams",
            "players": "/players",
            "games": "/games",
            "player_stats": "/player-stats",
            "top_scorers": "/stats/top-scorers/{season}",
            "team_record": "/stats/team-record/{season}",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
