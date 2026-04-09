"""
Statistics service - calculates and retrieves player statistics
Handles database queries and stat computations
"""
from sqlmodel import Session, select, func
from sqlalchemy import desc, and_
from typing import List, Dict, Optional, Tuple
from app.models import Player, PlayerSeason, Team
from app.schemas import PlayerSeasonRead
import logging

logger = logging.getLogger(__name__)

class StatsService:
    """Service for retrieving and calculating player statistics"""
    
    @staticmethod
    def get_top_scorers(session: Session, season: int, limit: int = 10) -> Tuple[List[Dict], str]:
        """
        Get top goal scorers for a season
        
        Args:
            session: Database session
            season: Season year
            limit: Number of results to return
            
        Returns:
            Tuple of (results list, SQL query string for learning)
        """
        query_string = f"""
SELECT 
    p.name,
    p.position,
    ps.goals,
    ps.assists,
    ps.points,
    ps.games_played
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE ps.season = {season}
ORDER BY ps.goals DESC
LIMIT {limit};
        """.strip()
        
        # Execute query
        statement = (
            select(Player.name, Player.position, PlayerSeason)
            .join(PlayerSeason)
            .where(PlayerSeason.season == season)
            .order_by(desc(PlayerSeason.goals))
            .limit(limit)
        )
        
        results = session.exec(statement).all()
        
        data = [
            {
                'name': r[0],
                'position': r[1],
                'goals': r[2].goals,
                'assists': r[2].assists,
                'points': r[2].points,
                'games_played': r[2].games_played
            }
            for r in results
        ]
        
        return data, query_string

    @staticmethod
    def get_top_point_getters(session: Session, season: int, limit: int = 10) -> Tuple[List[Dict], str]:
        """
        Get top point scorers (goals + assists)
        
        Args:
            session: Database session
            season: Season year
            limit: Number of results
            
        Returns:
            Tuple of (results list, SQL query string)
        """
        query_string = f"""
SELECT 
    p.name,
    p.position,
    ps.points,
    ps.goals,
    ps.assists,
    ps.games_played
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE ps.season = {season}
ORDER BY ps.points DESC
LIMIT {limit};
        """.strip()
        
        statement = (
            select(Player.name, Player.position, PlayerSeason)
            .join(PlayerSeason)
            .where(PlayerSeason.season == season)
            .order_by(desc(PlayerSeason.points))
            .limit(limit)
        )
        
        results = session.exec(statement).all()
        
        data = [
            {
                'name': r[0],
                'position': r[1],
                'points': r[2].points,
                'goals': r[2].goals,
                'assists': r[2].assists,
                'games_played': r[2].games_played
            }
            for r in results
        ]
        
        return data, query_string

    @staticmethod
    def get_most_penalized(session: Session, season: int, limit: int = 10) -> Tuple[List[Dict], str]:
        """
        Get players with most penalty minutes
        
        Args:
            session: Database session
            season: Season year
            limit: Number of results
            
        Returns:
            Tuple of (results list, SQL query string)
        """
        query_string = f"""
SELECT 
    p.name,
    p.position,
    ps.penalty_minutes,
    ps.games_played,
    ps.goals,
    ps.assists
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE ps.season = {season}
ORDER BY ps.penalty_minutes DESC
LIMIT {limit};
        """.strip()
        
        statement = (
            select(Player.name, Player.position, PlayerSeason)
            .join(PlayerSeason)
            .where(PlayerSeason.season == season)
            .order_by(desc(PlayerSeason.penalty_minutes))
            .limit(limit)
        )
        
        results = session.exec(statement).all()
        
        data = [
            {
                'name': r[0],
                'position': r[1],
                'penalty_minutes': r[2].penalty_minutes,
                'games_played': r[2].games_played,
                'goals': r[2].goals,
                'assists': r[2].assists
            }
            for r in results
        ]
        
        return data, query_string

    @staticmethod
    def get_player_by_name(session: Session, name: str) -> Tuple[Optional[Dict], str]:
        """
        Get player information by name
        
        Args:
            session: Database session
            name: Player name
            
        Returns:
            Tuple of (player dict or None, SQL query string)
        """
        query_string = f"""
SELECT 
    p.id,
    p.name,
    p.position,
    p.jersey_number,
    t.name as team_name,
    ps.season,
    ps.games_played,
    ps.goals,
    ps.assists,
    ps.points,
    ps.penalty_minutes,
    ps.plus_minus
FROM players p
LEFT JOIN teams t ON p.team_id = t.id
LEFT JOIN player_stats ps ON p.id = ps.player_id
WHERE p.name LIKE '%{name}%'
ORDER BY ps.season DESC;
        """.strip()
        
        statement = (
            select(Player)
            .where(Player.name.ilike(f"%{name}%"))
        )
        
        player = session.exec(statement).first()
        
        if not player:
            return None, query_string
        
        # Get player's stats
        stats_statement = (
            select(PlayerSeason)
            .where(PlayerSeason.player_id == player.id)
            .order_by(desc(PlayerSeason.season))
        )
        
        stats = session.exec(stats_statement).all()
        
        result = {
            'id': player.id,
            'name': player.name,
            'position': player.position,
            'jersey_number': player.jersey_number,
            'team': player.team.name if player.team else 'Unknown',
            'stats': [
                {
                    'season': s.season,
                    'games_played': s.games_played,
                    'goals': s.goals,
                    'assists': s.assists,
                    'points': s.points,
                    'penalty_minutes': s.penalty_minutes,
                    'plus_minus': s.plus_minus
                }
                for s in stats
            ]
        }
        
        return result, query_string

    @staticmethod
    def get_all_players(session: Session, season: Optional[int] = None) -> Tuple[List[Dict], str]:
        """
        Get all players, optionally filtered by season
        
        Args:
            session: Database session
            season: Optional season filter
            
        Returns:
            Tuple of (results list, SQL query string)
        """
        if season:
            query_string = f"""
SELECT DISTINCT
    p.id,
    p.name,
    p.position,
    p.jersey_number,
    t.name as team_name,
    ps.games_played,
    ps.goals,
    ps.assists,
    ps.points
FROM players p
LEFT JOIN teams t ON p.team_id = t.id
LEFT JOIN player_stats ps ON p.id = ps.player_id AND ps.season = {season}
ORDER BY p.name;
            """.strip()
            
            statement = (
                select(Player, Team, PlayerSeason)
                .outerjoin(Team)
                .outerjoin(PlayerSeason, and_(
                    Player.id == PlayerSeason.player_id,
                    PlayerSeason.season == season
                ))
                .order_by(Player.name)
            )
        else:
            query_string = """
SELECT DISTINCT
    p.id,
    p.name,
    p.position,
    p.jersey_number,
    t.name as team_name
FROM players p
LEFT JOIN teams t ON p.team_id = t.id
ORDER BY p.name;
            """.strip()
            
            statement = (
                select(Player, Team)
                .outerjoin(Team)
                .order_by(Player.name)
            )
        
        results = session.exec(statement).all()
        
        data = [
            {
                'id': r[0].id,
                'name': r[0].name,
                'position': r[0].position,
                'jersey_number': r[0].jersey_number,
                'team': r[1].name if r[1] else 'Unknown'
            }
            for r in results
        ]
        
        return data, query_string

    @staticmethod
    def get_season_leaders(session: Session, season: int) -> Dict[str, Tuple[List, str]]:
        """
        Get all leader categories for a season
        
        Args:
            session: Database session
            season: Season year
            
        Returns:
            Dictionary with leader data for each category
        """
        return {
            'scorers': StatsService.get_top_scorers(session, season, limit=10),
            'points': StatsService.get_top_point_getters(session, season, limit=10),
            'penalized': StatsService.get_most_penalized(session, season, limit=10)
        }

    @staticmethod
    def get_available_seasons(session: Session) -> List[int]:
        """
        Get list of available seasons in database
        
        Args:
            session: Database session
            
        Returns:
            List of season years
        """
        statement = select(func.distinct(PlayerSeason.season)).order_by(desc(PlayerSeason.season))
        seasons = session.exec(statement).all()
        return [s for s in seasons if s is not None]
