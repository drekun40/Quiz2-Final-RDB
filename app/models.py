"""
SQLAlchemy/SQLModel database models
Defines the schema for Teams, Players, and Stats
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Team(SQLModel, table=True):
    """Team model - represents an OHL team"""
    __tablename__ = "teams"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # e.g., "Erie Otters"
    city: str  # e.g., "Erie"
    league: str = "OHL"  # Hockey league
    code: str = Field(index=True)  # e.g., "EO" or "Erie"
    founded_year: Optional[int] = None
    
    # Relationship to players
    players: List["Player"] = Relationship(back_populates="team")
    
    def __repr__(self):
        return f"<Team {self.name} ({self.city})>"

class Player(SQLModel, table=True):
    """Player model - represents a hockey player"""
    __tablename__ = "players"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Full name
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id", index=True)
    position: str = Field(index=True)  # C, LW, RW, D, G, etc.
    birth_year: Optional[int] = None
    jersey_number: Optional[int] = None
    height: Optional[str] = None  # e.g., "5'11\""
    weight: Optional[int] = None  # in lbs
    
    # Relationship
    team: Optional[Team] = Relationship(back_populates="players")
    stats: List["PlayerSeason"] = Relationship(back_populates="player")
    
    def __repr__(self):
        return f"<Player {self.name} ({self.position})>"

class PlayerSeason(SQLModel, table=True):
    """PlayerSeason model - stats for a player in a specific season"""
    __tablename__ = "player_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="players.id", index=True)
    season: int = Field(index=True)  # e.g., 2024
    
    # Game stats
    games_played: int = 0
    goals: int = 0
    assists: int = 0
    points: int = 0  # goals + assists
    penalty_minutes: int = 0
    plus_minus: Optional[int] = None  # +/- rating if available
    
    # Metadata
    source_url: Optional[str] = None  # Where this data came from
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    player: Optional[Player] = Relationship(back_populates="stats")
    
    def __repr__(self):
        return f"<PlayerSeason {self.player_id} Season {self.season}: {self.goals}G {self.assists}A>"

class RefreshLog(SQLModel, table=True):
    """RefreshLog model - tracks when data was updated from source"""
    __tablename__ = "refresh_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source_url: str
    refresh_time: datetime = Field(default_factory=datetime.utcnow)
    status: str  # "success" or "error"
    record_count: int = 0
    error_message: Optional[str] = None
    
    def __repr__(self):
        return f"<RefreshLog {self.status} @ {self.refresh_time}>"
