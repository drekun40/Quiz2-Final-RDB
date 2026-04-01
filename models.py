from sqlmodel import SQLModel, Field, create_engine, Session, Relationship
from typing import Optional, List
from datetime import date

# Database URL
DATABASE_URL = "sqlite:///./erie_otters.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# ============================================================================
# Models
# ============================================================================

class Team(SQLModel, table=True):
    """Teams table"""
    team_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    founded_year: int
    league: str = "OHL"
    team_stats: List["TeamStats"] = Relationship(back_populates="team")


class Player(SQLModel, table=True):
    """Players table"""
    player_id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    birth_year: int
    position: str  # C, LW, RW, D, G
    draft_year: Optional[int] = None
    draft_team: Optional[str] = None
    player_stats: List["PlayerStats"] = Relationship(back_populates="player")


class Game(SQLModel, table=True):
    """Games table"""
    game_id: Optional[int] = Field(default=None, primary_key=True)
    season: int
    game_date: date
    home_team_id: int = Field(foreign_key="team.team_id")
    away_team_id: int = Field(foreign_key="team.team_id")
    home_score: int
    away_score: int
    venue: Optional[str] = None
    attendance: Optional[int] = None


class PlayerStats(SQLModel, table=True):
    """Player statistics per season"""
    stat_id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.player_id")
    season: int
    games_played: int
    goals: int
    assists: int
    points: int
    plus_minus: int
    penalty_minutes: int
    player: Player = Relationship(back_populates="player_stats")


class TeamStats(SQLModel, table=True):
    """Team statistics per season"""
    stat_id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.team_id")
    season: int
    wins: int
    losses: int
    ot_losses: int
    goals_for: int
    goals_against: int
    power_play_pct: float
    penalty_kill_pct: float
    team: Team = Relationship(back_populates="team_stats")


class Season(SQLModel, table=True):
    """Season information and summaries"""
    season_id: Optional[int] = Field(default=None, primary_key=True)
    season_year: int
    start_date: date
    end_date: date
    playoff_result: Optional[str] = None
    total_games: int


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session"""
    with Session(engine) as session:
        yield session
