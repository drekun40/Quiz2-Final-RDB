"""
Pydantic schemas - for request/response validation
These are separate from SQLModel for API responses
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# ==================== Team Schemas ====================
class TeamBase(BaseModel):
    """Base team information"""
    name: str
    city: str
    code: str
    league: str = "OHL"
    founded_year: Optional[int] = None

class TeamRead(TeamBase):
    """Team response from API"""
    id: int

    class Config:
        from_attributes = True

class TeamCreate(TeamBase):
    """Data needed to create a team"""
    pass

# ==================== Player Schemas ====================
class PlayerBase(BaseModel):
    """Base player information"""
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: str
    team_id: Optional[int] = None
    birth_year: Optional[int] = None
    jersey_number: Optional[int] = None

class PlayerRead(PlayerBase):
    """Player response from API"""
    id: int

    class Config:
        from_attributes = True

class PlayerCreate(PlayerBase):
    """Data needed to create a player"""
    pass

# ==================== Player Season Stats Schemas ====================
class PlayerSeasonBase(BaseModel):
    """Base stats for a player-season"""
    player_id: int
    season: int
    games_played: int
    goals: int
    assists: int
    points: int
    penalty_minutes: int = 0
    plus_minus: Optional[int] = None

class PlayerSeasonRead(PlayerSeasonBase):
    """Player season stats response"""
    id: int
    source_url: Optional[str] = None
    scraped_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlayerSeasonCreate(PlayerSeasonBase):
    """Data needed to create player season stats"""
    source_url: Optional[str] = None

# ==================== Combined Response Schemas ====================
class PlayerWithTeam(PlayerRead):
    """Player data with team information"""
    team: Optional[TeamRead] = None

class PlayerWithStats(PlayerRead):
    """Player with their season statistics"""
    stats: List[PlayerSeasonRead] = []

# ==================== Query Schemas ====================
class QueryInfo(BaseModel):
    """Information about DB query for learning"""
    query_string: str
    explanation: str
    table_name: str

class PageContext(BaseModel):
    """Context data for template rendering"""
    title: str
    query_info: Optional[QueryInfo] = None
    data: dict
