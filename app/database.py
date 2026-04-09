"""
Database configuration and connection setup
Supports multiple databases - one per season
"""
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Current season (2019 is the latest in our data)
CURRENT_SEASON = 2019
AVAILABLE_SEASONS = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
COMPLETED_SEASONS = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]

# Engine cache for each season
_engines = {}

def get_database_url(season: int) -> str:
    """Get database URL for a specific season"""
    return f"sqlite:///{BASE_DIR}/erie_otters_{season}.db"

def get_engine(season: int = None):
    """Get or create database engine for a season"""
    if season is None:
        season = CURRENT_SEASON
    
    if season not in _engines:
        db_url = get_database_url(season)
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        _engines[season] = engine
        SQLModel.metadata.create_all(engine)
    
    return _engines[season]

def create_db_and_tables(season: int = None):
    """Create all database tables for a season"""
    engine = get_engine(season)
    SQLModel.metadata.create_all(engine)

def get_session(season: int = None):
    """Dependency to get database session for routes"""
    engine = get_engine(season)
    with Session(engine) as session:
        yield session

def is_season_completed(season: int) -> bool:
    """Check if a season is completed (no predictions, show analysis instead)"""
    return season in COMPLETED_SEASONS

# Initialize database on module import
get_engine()
