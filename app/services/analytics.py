"""
Analytics service - provides analysis for completed seasons
Instead of predictions, shows real season data analysis
"""

from sqlmodel import Session, select, func
from sqlalchemy import desc
from app.models import Player, PlayerSeason
from typing import Dict, List, Optional

class AnalyticsService:
    """Service for providing season analysis"""
    
    @staticmethod
    def get_season_summary(session: Session, season: int) -> Dict:
        """Get overall season statistics and analysis"""
        
        # Get all stats for the season
        all_stats = session.exec(
            select(PlayerSeason).where(PlayerSeason.season == season)
        ).all()
        
        if not all_stats:
            return {}
        
        total_goals = sum(s.goals for s in all_stats)
        total_assists = sum(s.assists for s in all_stats)
        total_points = sum(s.points for s in all_stats)
        total_pim = sum(s.penalty_minutes for s in all_stats)
        total_gp = sum(s.games_played for s in all_stats)
        
        avg_goals_per_player = total_goals / len(all_stats) if all_stats else 0
        avg_points_per_player = total_points / len(all_stats) if all_stats else 0
        
        return {
            'season': season,
            'total_players': len(all_stats),
            'total_goals': total_goals,
            'total_assists': total_assists,
            'total_points': total_points,
            'total_pim': total_pim,
            'total_gp': total_gp,
            'avg_goals_per_player': round(avg_goals_per_player, 2),
            'avg_assists_per_player': round(total_assists / len(all_stats), 2),
            'avg_points_per_player': round(avg_points_per_player, 2),
            'avg_pim_per_player': round(total_pim / len(all_stats), 2),
        }
    
    @staticmethod
    def get_season_insights(session: Session, season: int) -> List[Dict]:
        """Get interesting insights about the season"""
        
        all_stats = session.exec(
            select(Player.name, Player.position, PlayerSeason)
            .join(PlayerSeason)
            .where(PlayerSeason.season == season)
        ).all()
        
        if not all_stats:
            return []
        
        insights = []
        
        # Best scorer
        best_scorer = max(all_stats, key=lambda x: x[2].goals)
        insights.append({
            'type': 'top_scorer',
            'title': '⚽ Top Goal Scorer',
            'player': best_scorer[0],
            'value': best_scorer[2].goals,
            'stat': 'goals',
        })
        
        # Best point producer
        best_producer = max(all_stats, key=lambda x: x[2].points)
        insights.append({
            'type': 'top_points',
            'title': '🎯 Top Point Producer',
            'player': best_producer[0],
            'value': best_producer[2].points,
            'stat': 'points',
        })
        
        # Most penalized
        most_penalized = max(all_stats, key=lambda x: x[2].penalty_minutes)
        insights.append({
            'type': 'most_penalized',
            'title': '⚠️ Most Penalized',
            'player': most_penalized[0],
            'value': most_penalized[2].penalty_minutes,
            'stat': 'PIM',
        })
        
        # Most assists
        best_assister = max(all_stats, key=lambda x: x[2].assists)
        insights.append({
            'type': 'top_assists',
            'title': '🤝 Top Playmaker',
            'player': best_assister[0],
            'value': best_assister[2].assists,
            'stat': 'assists',
        })
        
        # Efficiency (goals per game)
        active_players = [s for s in all_stats if s[2].games_played > 0]
        if active_players:
            best_efficiency = max(active_players, key=lambda x: x[2].goals / max(x[2].games_played, 1))
            insights.append({
                'type': 'efficiency',
                'title': '🔥 Most Efficient (Goals/GP)',
                'player': best_efficiency[0],
                'value': round(best_efficiency[2].goals / best_efficiency[2].games_played, 2),
                'stat': 'Goals/GP',
            })
        
        return insights
    
    @staticmethod
    def get_position_analysis(session: Session, season: int) -> Dict:
        """Get analysis by position"""
        
        stats_by_pos = session.exec(
            select(Player.position, func.count(PlayerSeason.id).label('count'),
                   func.sum(PlayerSeason.goals).label('total_goals'),
                   func.sum(PlayerSeason.points).label('total_points'),
                   func.avg(PlayerSeason.points).label('avg_points'))
            .select_from(Player)
            .join(PlayerSeason)
            .where(PlayerSeason.season == season)
            .group_by(Player.position)
        ).all()
        
        analysis = {}
        for pos, count, goals, points, avg_points in stats_by_pos:
            analysis[pos] = {
                'position': pos,
                'player_count': count,
                'total_goals': goals or 0,
                'total_points': points or 0,
                'avg_points': round(avg_points or 0, 2),
            }
        
        return analysis
    
    @staticmethod
    def get_season_trends(session: Session, season_list: List[int]) -> Dict:
        """Compare trends across multiple seasons"""
        
        trends = {}
        
        for season in season_list:
            summary = AnalyticsService.get_season_summary(session, season)
            trends[season] = summary
        
        return trends
