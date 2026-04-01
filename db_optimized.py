import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd


class OptimizedDatabase:
    """Optimized database operations for Erie Otters data"""

    def __init__(self, db_path: str = "erie_otters.db"):
        self.db_path = Path(db_path)
        self.conn = None

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_player_season_stats(self, player_id: int, season: int) -> Dict[str, Any]:
        """Get a player's stats for a specific season"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        query = """
            SELECT p.first_name, p.last_name, ps.*
            FROM players p
            JOIN player_stats ps ON p.player_id = ps.player_id
            WHERE p.player_id = ? AND ps.season = ?
        """
        cursor.execute(query, (player_id, season))
        result = cursor.fetchone()
        return dict(result) if result else None

    def get_team_season_summary(self, team_id: int, season: int) -> Dict[str, Any]:
        """Get team summary for a season"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        query = """
            SELECT t.name, ts.*
            FROM teams t
            JOIN team_stats ts ON t.team_id = ts.team_id
            WHERE t.team_id = ? AND ts.season = ?
        """
        cursor.execute(query, (team_id, season))
        result = cursor.fetchone()
        return dict(result) if result else None

    def get_top_goal_scorers(self, season: int, limit: int = 10) -> List[Dict]:
        """Get top goal scorers for a season"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        query = """
            SELECT p.player_id, p.first_name, p.last_name, 
                   ps.goals, ps.assists, ps.points, ps.games_played
            FROM players p
            JOIN player_stats ps ON p.player_id = ps.player_id
            WHERE ps.season = ?
            ORDER BY ps.goals DESC
            LIMIT ?
        """
        cursor.execute(query, (season, limit))
        results = [dict(row) for row in cursor.fetchall()]
        return results

    def get_games_by_season(self, season: int) -> List[Dict]:
        """Get all games for a season"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        query = """
            SELECT g.*, ht.name as home_team_name, at.name as away_team_name
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams at ON g.away_team_id = at.team_id
            WHERE g.season = ?
            ORDER BY g.game_date
        """
        cursor.execute(query, (season,))
        results = [dict(row) for row in cursor.fetchall()]
        return results

    def get_player_career_stats(self, player_id: int) -> List[Dict]:
        """Get all seasons stats for a player"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        query = """
            SELECT ps.*, p.first_name, p.last_name
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.player_id
            WHERE ps.player_id = ?
            ORDER BY ps.season DESC
        """
        cursor.execute(query, (player_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results

    def export_to_csv(self, query: str, output_path: str):
        """Export query results to CSV"""
        if not self.conn:
            self.connect()

        df = pd.read_sql_query(query, self.conn)
        df.to_csv(output_path, index=False)
        print(f"Data exported to {output_path}")

    def create_indexes(self):
        """Create indexes for better query performance"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_player_stats_season ON player_stats(season)",
            "CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_stats(player_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_stats_season ON team_stats(season)",
            "CREATE INDEX IF NOT EXISTS idx_games_season ON games(season)",
            "CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date)",
        ]

        for idx in indexes:
            cursor.execute(idx)

        self.conn.commit()
        print("Indexes created successfully")


if __name__ == "__main__":
    db = OptimizedDatabase()
    db.connect()
    db.create_indexes()
    db.close()
