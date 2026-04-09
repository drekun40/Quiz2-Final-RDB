"""
Simple prediction service for learning
Uses basic pace projections to estimate end-of-season stats
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# OHL season length (approximate regular season games)
# Season can vary: typically 66-82 games
SEASON_LENGTH = 64  # Adjust based on actual OHL season

class PredictorService:
    """
    Simple prediction service for learning purposes
    Uses pace-based projections
    """
    
    @staticmethod
    def calculate_pace_projection(
        current_stat: int,
        games_played: int,
        season_length: int = SEASON_LENGTH
    ) -> int:
        """
        Calculate projection based on current pace
        
        This is a simple learning model, not a production predictor!
        
        Formula:
            projected_stat = (current_stat / games_played) * season_length
        
        Args:
            current_stat: Current season stat (goals, assists, points, etc.)
            games_played: Games played so far
            season_length: Total season games
            
        Returns:
            Projected end-of-season stat
        """
        if games_played == 0:
            return 0
        
        pace = current_stat / games_played
        projection = int(pace * season_length)
        
        return projection

    @staticmethod
    def project_player_season(player_stats: Dict) -> Dict:
        """
        Project end-of-season stats for a player
        
        This is for LEARNING purposes only!
        Do NOT use for actual predictions or betting.
        
        Args:
            player_stats: Dictionary with current season stats
                Expected keys: goals, assists, points, games_played, penalty_minutes
                
        Returns:
            Dictionary with projected stats
        """
        if player_stats.get('games_played', 0) == 0:
            return {
                'note': 'No games played yet',
                'projected_goals': 0,
                'projected_assists': 0,
                'projected_points': 0,
                'projected_pim': 0,
                'games_played': 0,
                'season_length': SEASON_LENGTH
            }
        
        gp = player_stats.get('games_played', 0)
        
        # Calculate projections for key stats
        proj_goals = PredictorService.calculate_pace_projection(
            player_stats.get('goals', 0),
            gp,
            SEASON_LENGTH
        )
        
        proj_assists = PredictorService.calculate_pace_projection(
            player_stats.get('assists', 0),
            gp,
            SEASON_LENGTH
        )
        
        proj_points = PredictorService.calculate_pace_projection(
            player_stats.get('points', 0),
            gp,
            SEASON_LENGTH
        )
        
        proj_pim = PredictorService.calculate_pace_projection(
            player_stats.get('penalty_minutes', 0),
            gp,
            SEASON_LENGTH
        )
        
        return {
            'projected_goals': proj_goals,
            'projected_assists': proj_assists,
            'projected_points': proj_points,
            'projected_pim': proj_pim,
            'current_pace': {
                'goals_per_game': round(player_stats.get('goals', 0) / gp, 2) if gp > 0 else 0,
                'assists_per_game': round(player_stats.get('assists', 0) / gp, 2) if gp > 0 else 0,
                'points_per_game': round(player_stats.get('points', 0) / gp, 2) if gp > 0 else 0,
            },
            'games_played': gp,
            'season_length': SEASON_LENGTH,
            'disclaimer': 'This is a simple learning projection based on current pace. ' \
                         'It does NOT account for injuries, trades, lineup changes, ' \
                         'or other real-world factors that affect player performance.'
        }

    @staticmethod
    def get_prediction_explanation() -> str:
        """Get friendly explanation of how predictions work"""
        return f"""
        <div style="background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3 style="color: #0b1f41; margin-top: 0;">📚 Learning: How Does This Projection Work?</h3>
            
            <p><strong>Simple Pace Formula:</strong></p>
            <code style="background: white; padding: 10px; display: block; border-radius: 3px;">
                Projected Stat = (Current Stat ÷ Games Played) × {SEASON_LENGTH} Games
            </code>
            
            <p><strong>Example:</strong></p>
            <p>If a player has scored 12 goals in 20 games:</p>
            <code style="background: white; padding: 10px; display: block; border-radius: 3px;">
                Projected Goals = (12 ÷ 20) × {SEASON_LENGTH} = 0.6 × {SEASON_LENGTH} = <strong>{int(0.6 * SEASON_LENGTH)}</strong>
            </code>
            
            <p><strong>⚠️ Important Disclaimer:</strong></p>
            <ul>
                <li>This is a <strong>simple learning model</strong>, not a professional prediction</li>
                <li>It only uses current pace and assumes consistent performance</li>
                <li>It does NOT account for:</li>
                <ul>
                    <li>Injuries or suspensions</li>
                    <li>Trades or lineup changes</li>
                    <li>Opposing team strength</li>
                    <li>Playoff intensity vs regular season</li>
                    <li>Any real-world complications</li>
                </ul>
            </ul>
            
            <p><strong>Better Uses:</strong></p>
            <ul>
                <li>Learn SQL and data analysis basics</li>
                <li>Understand how pace calculations work</li>
                <li>Compare different players' trajectories</li>
                <li>Build your first data model</li>
            </ul>
        </div>
        """
