"""
Deduplication helpers for handling duplicate player records within seasons
"""
from sqlmodel import Session, select
from sqlalchemy import func, and_
from app.models import Player, PlayerSeason, Team
from typing import List, Dict, Tuple


class DeduplicationService:
    """Service for detecting and preparing deduplication of player records"""
    
    @staticmethod
    def get_unique_players_in_season(session: Session, season: int = None) -> List[Player]:
        """
        Get unique players for a season, using the record with lowest ID as primary
        
        This is the safe way to query players when duplicates exist in the DB.
        Returns only one Player object per player name.
        
        Args:
            session: SQLAlchemy session for the database
            season: Optional season to filter by (currently ignored - returns all unique players)
        
        Returns:
            List of Player objects, deduplicated by name (lowest ID retained)
        """
        # Get all players, group by name, keep only lowest ID
        stmt = select(Player).distinct(Player.name)
        players = session.exec(stmt).all()
        
        # Manual deduplication by name (keeping first occurrence)
        seen = {}
        unique_players = []
        
        for player in players:
            if player.name not in seen:
                seen[player.name] = player
                unique_players.append(player)
        
        return sorted(unique_players, key=lambda p: p.name)
    
    @staticmethod
    def get_player_by_name_unique(session: Session, player_name: str) -> Player:
        """
        Get a single player by name, safely handling duplicates.
        If multiple records exist, returns the one with lowest ID.
        
        Args:
            session: SQLAlchemy session
            player_name: Name of the player to find
        
        Returns:
            Player object or None if not found
        """
        stmt = select(Player).where(
            Player.name == player_name
        ).order_by(Player.id.asc())
        
        players_with_name = session.exec(stmt).all()
        
        if not players_with_name:
            return None
        
        # Return the one with lowest ID (primary record)
        return players_with_name[0]
    
    @staticmethod
    def find_duplicate_players(session: Session) -> Dict[str, List[int]]:
        """
        Find all duplicate player names in the database.
        
        Returns:
            Dict mapping player name to list of player IDs that have that name
            Only includes names that appear more than once
        
        Example:
            {
                "Brendan Brisson": [1, 4, 14],
                "Jack Perbix": [2, 5, 15]
            }
        """
        # Query all players
        all_players = session.exec(select(Player)).all()
        
        # Group by name
        name_to_ids = {}
        for player in all_players:
            if player.name not in name_to_ids:
                name_to_ids[player.name] = []
            name_to_ids[player.name].append(player.id)
        
        # Filter to only those with duplicates
        duplicates = {
            name: ids 
            for name, ids in name_to_ids.items() 
            if len(ids) > 1
        }
        
        return duplicates
    
    @staticmethod
    def count_duplicates(session: Session) -> Tuple[int, int, int]:
        """
        Count total, unique, and duplicate player records.
        
        Returns:
            Tuple of (total_count, unique_count, duplicate_count)
        """
        all_players = session.exec(select(Player)).all()
        total_count = len(all_players)
        
        unique_names = set(p.name for p in all_players)
        unique_count = len(unique_names)
        
        duplicate_count = total_count - unique_count
        
        return (total_count, unique_count, duplicate_count)
    
    @staticmethod
    def get_duplicate_ids_to_delete(session: Session) -> List[int]:
        """
        Get list of player IDs that should be deleted (duplicates, keeping lowest ID).
        
        Returns:
            List of player IDs to delete (all but the lowest ID for each name)
        """
        duplicates = DeduplicationService.find_duplicate_players(session)
        
        ids_to_delete = []
        for player_name, ids in duplicates.items():
            # Keep the lowest ID, mark rest for deletion
            sorted_ids = sorted(ids)
            id_to_keep = sorted_ids[0]
            ids_to_delete.extend(sorted_ids[1:])  # All except the first
        
        return ids_to_delete
    
    @staticmethod
    def get_duplicate_player_stats(session: Session, player_id: int) -> List[PlayerSeason]:
        """
        Get all stat records for a player (useful for verifying duplicates have same stats).
        
        Args:
            session: SQLAlchemy session
            player_id: The player ID
        
        Returns:
            List of PlayerSeason records for this player_id
        """
        stmt = select(PlayerSeason).where(
            PlayerSeason.player_id == player_id
        ).order_by(PlayerSeason.season)
        
        return session.exec(stmt).all()
    
    @staticmethod
    def validate_duplicate_stats_are_identical(session: Session, player_name: str) -> bool:
        """
        For a player with duplicates, validate that all duplicate records have identical stats.
        This is important for detecting whether duplicates are real data duplication.
        
        Args:
            session: SQLAlchemy session
            player_name: Name of player with duplicates
        
        Returns:
            True if all stats are identical, False otherwise
        """
        # Get all players with this name
        stmt = select(Player).where(Player.name == player_name)
        players = session.exec(stmt).all()
        
        if len(players) <= 1:
            return True  # No duplicates, so true
        
        # Get stats for each player
        all_stats = {}
        for player in players:
            stats_list = DeduplicationService.get_duplicate_player_stats(session, player.id)
            all_stats[player.id] = {
                (s.season, s.games_played, s.goals, s.assists, s.points, s.penalty_minutes)
                for s in stats_list
            }
        
        # Compare all to first
        first_stats = all_stats[players[0].id]
        
        for player_id, stats in all_stats.items():
            if stats != first_stats:
                return False  # Stats differ
        
        return True  # All identical
