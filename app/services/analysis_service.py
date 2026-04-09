"""
Analysis service - generates insights and statistics from player data
Computes season analysis, career trends, performance metrics, etc.
"""
from sqlmodel import Session, select
from sqlalchemy import func, desc
from typing import Dict, List, Optional, Tuple
from app.models import Player, PlayerSeason
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for generating player and season analysis insights"""
    
    @staticmethod
    def get_player_career_stats(sessions: Dict[int, Session], player_name: str) -> Dict:
        """
        Get comprehensive career stats for a player across all seasons
        
        Args:
            sessions: Dictionary of {season: Session} for all available seasons
            player_name: Name of the player
            
        Returns:
            Dictionary with career statistics and analysis
        """
        all_seasons = []
        career_totals = {
            'games_played': 0,
            'goals': 0,
            'assists': 0,
            'points': 0,
            'penalty_minutes': 0,
        }
        
        # Collect stats from all seasons
        for season, session in sorted(sessions.items()):
            statement = (
                select(Player, PlayerSeason)
                .join(PlayerSeason)
                .where(Player.name == player_name)
                .where(PlayerSeason.season == season)
            )
            result = session.exec(statement).first()
            
            if result:
                player, season_stats = result
                season_data = {
                    'season': season,
                    'games_played': season_stats.games_played,
                    'goals': season_stats.goals,
                    'assists': season_stats.assists,
                    'points': season_stats.points,
                    'penalty_minutes': season_stats.penalty_minutes,
                    'ppg': round(season_stats.points / season_stats.games_played, 2) if season_stats.games_played > 0 else 0,
                }
                all_seasons.append(season_data)
                
                # Add to career totals
                career_totals['games_played'] += season_stats.games_played
                career_totals['goals'] += season_stats.goals
                career_totals['assists'] += season_stats.assists
                career_totals['points'] += season_stats.points
                career_totals['penalty_minutes'] += season_stats.penalty_minutes
        
        if not all_seasons:
            return {}
        
        # Calculate career PPG
        career_ppg = round(career_totals['points'] / career_totals['games_played'], 2) if career_totals['games_played'] > 0 else 0
        
        # Find best season
        best_season = max(all_seasons, key=lambda x: x['points'])
        worst_season = min(all_seasons, key=lambda x: x['points'])
        
        # Calculate improvement (first to last season)
        first_season = all_seasons[0]
        last_season = all_seasons[-1]
        improvement = last_season['ppg'] - first_season['ppg']
        
        # Calculate consistency (standard deviation of PPG)
        ppg_values = [s['ppg'] for s in all_seasons]
        avg_ppg = sum(ppg_values) / len(ppg_values)
        variance = sum((x - avg_ppg) ** 2 for x in ppg_values) / len(ppg_values)
        consistency_score = round(variance ** 0.5, 2)  # Lower is more consistent
        
        # Goals vs assists ratio
        goals_assists_ratio = round(career_totals['goals'] / career_totals['assists'], 2) if career_totals['assists'] > 0 else 0
        
        analysis = {
            'career_totals': career_totals,
            'career_ppg': career_ppg,
            'seasons_count': len(all_seasons),
            'best_season': {
                'year': best_season['season'],
                'points': best_season['points'],
                'ppg': best_season['ppg'],
            },
            'worst_season': {
                'year': worst_season['season'],
                'points': worst_season['points'],
                'ppg': worst_season['ppg'],
            },
            'improvement_ppg': round(improvement, 2),
            'consistency_variance': consistency_score,
            'goals_per_assist_ratio': goals_assists_ratio,
            'avg_goals_per_season': round(career_totals['goals'] / len(all_seasons), 1),
            'avg_assists_per_season': round(career_totals['assists'] / len(all_seasons), 1),
        }
        
        return {
            'player_name': player_name,
            'all_seasons': all_seasons,
            'analysis': analysis,
        }
    
    @staticmethod
    def generate_player_summary_text(analysis_data: Dict) -> str:
        """
        Generate human-readable analysis summary from career stats
        
        Args:
            analysis_data: Output from get_player_career_stats
            
        Returns:
            HTML string with analysis summary
        """
        if not analysis_data or 'analysis' not in analysis_data:
            return ""
        
        a = analysis_data['analysis']
        player = analysis_data['player_name']
        
        summary_parts = [
            f"<div class='analysis-text'>",
            f"<h3>Career Analysis</h3>",
            f"<p><strong>{player}</strong> played {a['seasons_count']} seasons with the Erie Otters, "
            f"accumulating {a['career_totals']['points']} total points ({a['career_totals']['goals']} G, "
            f"{a['career_totals']['assists']} A) in {a['career_totals']['games_played']} games.</p>",
        ]
        
        # Best season insight
        best = a['best_season']
        summary_parts.append(
            f"<p><strong>Best Season:</strong> {best['year']}-{best['year']+1} with {best['points']} points "
            f"({best['ppg']} PPG).</p>"
        )
        
        # Improvement insight
        if a['improvement_ppg'] > 0:
            summary_parts.append(
                f"<p><strong>Trend:</strong> {player} showed improvement, increasing production by "
                f"{a['improvement_ppg']} points per game from first to last season.</p>"
            )
        elif a['improvement_ppg'] < 0:
            summary_parts.append(
                f"<p><strong>Trend:</strong> {player}'s scoring declined by {abs(a['improvement_ppg'])} "
                f"points per game from first to last season.</p>"
            )
        else:
            summary_parts.append(
                f"<p><strong>Trend:</strong> {player}'s per-game scoring remained consistent across seasons.</p>"
            )
        
        # Consistency insight
        if a['consistency_variance'] < 0.5:
            consistency = "very consistent"
        elif a['consistency_variance'] < 1.0:
            consistency = "fairly consistent"
        else:
            consistency = "variable"
        
        summary_parts.append(
            f"<p><strong>Consistency:</strong> {player} was {consistency} across seasons "
            f"(variance: {a['consistency_variance']}).</p>"
        )
        
        # Playing style insight
        if a['goals_per_assist_ratio'] > 1.2:
            style = "goal scorer"
        elif a['goals_per_assist_ratio'] < 0.8:
            style = "playmaker"
        else:
            style = "balanced scorer"
        
        summary_parts.append(
            f"<p><strong>Playing Style:</strong> {player} was a {style} with a "
            f"{a['goals_per_assist_ratio']} goals-to-assists ratio.</p>"
        )
        
        summary_parts.append("</div>")
        
        return "\n".join(summary_parts)
    
    @staticmethod
    def get_season_overview(session: Session, season: int) -> Dict:
        """
        Get overview statistics for a season
        
        Args:
            session: Database session
            season: Season year
            
        Returns:
            Dictionary with season overview stats
        """
        statement = select(PlayerSeason).where(PlayerSeason.season == season)
        all_stats = session.exec(statement).all()
        
        if not all_stats:
            return {}
        
        total_goals = sum(s.goals for s in all_stats)
        total_assists = sum(s.assists for s in all_stats)
        total_points = sum(s.points for s in all_stats)
        total_gp = sum(s.games_played for s in all_stats)
        total_pim = sum(s.penalty_minutes for s in all_stats)
        
        avg_ppg = round(total_points / len(all_stats), 2) if all_stats else 0
        
        return {
            'season': season,
            'player_count': len(all_stats),
            'total_goals': total_goals,
            'total_assists': total_assists,
            'total_points': total_points,
            'total_gp': total_gp,
            'total_pim': total_pim,
            'avg_ppg': avg_ppg,
        }
    
    @staticmethod
    def get_top_performers(session: Session, season: int, limit: int = 10) -> List[Dict]:
        """
        Get top point getters for a season with performance metrics
        
        Args:
            session: Database session
            season: Season year
            limit: Number of results
            
        Returns:
            List of top performers with calculated metrics
        """
        statement = (
            select(Player, PlayerSeason)
            .join(PlayerSeason)
            .where(PlayerSeason.season == season)
            .order_by(desc(PlayerSeason.points))
            .limit(limit)
        )
        
        results = session.exec(statement).all()
        
        performers = []
        for player, season_stats in results:
            ppg = round(season_stats.points / season_stats.games_played, 2) if season_stats.games_played > 0 else 0
            performers.append({
                'name': player.name,
                'position': player.position,
                'goals': season_stats.goals,
                'assists': season_stats.assists,
                'points': season_stats.points,
                'games_played': season_stats.games_played,
                'ppg': ppg,
                'player_id': player.id,
            })
        
        return performers
