"""
Route handlers for all pages
Handles rendering of templates and data retrieval
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy import func, desc
from app.database import get_session, get_engine, AVAILABLE_SEASONS, CURRENT_SEASON, is_season_completed
from app.models import Team, Player, PlayerSeason, RefreshLog
from app.services.stats_service import StatsService
from app.services.analytics import AnalyticsService as OldAnalyticsService
from app.services.analysis_service import AnalysisService
from app.services.scraper import ErieScraper
from app.services.predictor import PredictorService
from app.services.deduplication import DeduplicationService
from datetime import datetime
import logging
import os
import json
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

# Setup Jinja2 environment  
APP_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = APP_DIR / "templates"

if TEMPLATES_DIR.exists():
    jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        cache_size=0  # Disable caching to avoid the unhashable type error
    )
    logger.info(f"Jinja2 environment initialized from {TEMPLATES_DIR}")
else:
    logger.error(f"Templates directory not found: {TEMPLATES_DIR}")
    raise RuntimeError(f"Templates directory not found at {TEMPLATES_DIR}")

def render_template(template_name: str, context: dict) -> HTMLResponse:
    """Render a template directly with Jinja2"""
    try:
        template = jinja_env.get_template(template_name)
        html_content = template.render(**context)
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Failed to render template: {template_name}</p><pre>{str(e)}</pre>",
            status_code=500
        )

# ==================== HOMEPAGE ====================

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, season: str = str(CURRENT_SEASON)):
    """
    Homepage - Welcome dashboard with season selector
    Shows overview and quick links
    """
    # Handle "all" seasons
    if season.lower() == "all" or season == "0":
        total_player_count = 0
        total_team_count = 0
        
        for season_num in AVAILABLE_SEASONS:
            engine = get_engine(season_num)
            session = Session(engine)
            try:
                player_count = session.query(Player).count()
                team_count = session.query(Team).count()
                total_player_count += player_count
                total_team_count += team_count
            finally:
                session.close()
        
        # Average across seasons
        avg_players = round(total_player_count / len(AVAILABLE_SEASONS)) if AVAILABLE_SEASONS else 0
        
        query_string = """
-- Overview across all 10 seasons  
SELECT COUNT(DISTINCT season) as seasons_count,
       COUNT(DISTINCT p.id) as unique_players,
       COUNT(*) as total_records
FROM players p
JOIN player_stats ps ON p.id = ps.player_id;
        """.strip()
        
        context = {
            'request': request,
            'title': 'Erie Otters Stats Hub - Career Overview',
            'player_count': avg_players,
            'team_count': total_team_count // len(AVAILABLE_SEASONS) if AVAILABLE_SEASONS else 0,
            'current_season': 'all',
            'available_seasons': AVAILABLE_SEASONS,
            'season_label': f"All Seasons Career Stats",
            'query_string': query_string,
            'debug': os.getenv("ENV", "development") == "development"
        }
        
        return render_template("index.html", context)
    else:
        # Single season mode
        try:
            season_num = int(season)
        except (ValueError, TypeError):
            season_num = CURRENT_SEASON
        
        if season_num not in AVAILABLE_SEASONS:
            season_num = CURRENT_SEASON
        
        # Get engine for this season
        engine = get_engine(season_num)
        session = Session(engine)
        
        try:
            # Get some basic stats for the dashboard
            player_count = session.query(Player).count()
            team_count = session.query(Team).count()
            
            # Query string for learning
            query_string = f"""
SELECT COUNT(*) as player_count FROM players;
SELECT COUNT(*) as team_count FROM teams;
-- Season {season_num} roster statistics
            """.strip()
            
            context = {
                'request': request,
                'title': 'Erie Otters Stats Hub',
                'player_count': player_count,
                'team_count': team_count,
                'current_season': season_num,
                'available_seasons': AVAILABLE_SEASONS,
                'season_label': f"{season_num}-{season_num+1}" if season_num != CURRENT_SEASON else f"{season_num}-{season_num+1} (Current)",
                'query_string': query_string,
                'debug': os.getenv("ENV", "development") == "development"
            }
            
            return render_template("index.html", context)
        finally:
            session.close()

# ==================== LEADERS PAGE ====================

@router.get("/leaders", response_class=HTMLResponse)
async def leaders(
    request: Request,
    season: str = str(CURRENT_SEASON)
):
    """
    Season leaders/analysis page
    Shows leaderboards for single season or all seasons combined
    """
    # Handle "all" seasons
    if season.lower() == "all" or season == "0":
        # Aggregate leaders from all seasons
        all_scorers = {}
        all_points = {}
        all_penalized = {}
        
        for season_num in AVAILABLE_SEASONS:
            engine = get_engine(season_num)
            session = Session(engine)
            
            try:
                leaders_data = StatsService.get_season_leaders(session, season_num)
                
                # Aggregate scorers
                for scorer in leaders_data['scorers'][0]:
                    name = scorer.get('name') or scorer.get('player_name', '')
                    if name not in all_scorers:
                        all_scorers[name] = {
                            'name': name,
                            'goals': 0,
                            'position': scorer.get('position', '-')
                        }
                    all_scorers[name]['goals'] += scorer.get('goals', 0)
                
                # Aggregate points
                for pts in leaders_data['points'][0]:
                    name = pts.get('name') or pts.get('player_name', '')
                    if name not in all_points:
                        all_points[name] = {
                            'name': name,
                            'points': 0,
                            'position': pts.get('position', '-')
                        }
                    all_points[name]['points'] += pts.get('points', 0)
                
                # Aggregate penalized
                for pen in leaders_data['penalized'][0]:
                    name = pen.get('name') or pen.get('player_name', '')
                    if name not in all_penalized:
                        all_penalized[name] = {
                            'name': name,
                            'penalty_minutes': 0,
                            'position': pen.get('position', '-')
                        }
                    all_penalized[name]['penalty_minutes'] += pen.get('penalty_minutes', 0)
            finally:
                session.close()
        
        # Convert dicts to sorted lists
        top_scorers_data = sorted(all_scorers.values(), key=lambda x: x['goals'], reverse=True)[:10]
        top_points_data = sorted(all_points.values(), key=lambda x: x['points'], reverse=True)[:10]
        top_penalized_data = sorted(all_penalized.values(), key=lambda x: x['penalty_minutes'], reverse=True)[:10]
        
        context = {
            'request': request,
            'title': 'Career Leaderboards',
            'season': 'all',
            'current_season': 'all',
            'season_label': 'Career Stats (All 10 Seasons)',
            'available_seasons': AVAILABLE_SEASONS,
            'is_completed': True,
            'scorers': top_scorers_data,
            'scorers_query': '-- Top career goal scorers across all seasons',
            'points': top_points_data,
            'points_query': '-- Top career point leaders across all seasons',
            'penalized': top_penalized_data,
            'penalized_query': '-- Most penalized players across all seasons',
        }
        
        return render_template("leaders.html", context)
    else:
        # Single season mode
        try:
            season_num = int(season)
        except (ValueError, TypeError):
            season_num = CURRENT_SEASON
        
        if season_num not in AVAILABLE_SEASONS:
            season_num = CURRENT_SEASON
        
        engine = get_engine(season_num)
        session = Session(engine)
        
        try:
            # Show leaderboards for single season
            try:
                leaders_data = StatsService.get_season_leaders(session, season_num)
                top_scorers_data, scorers_query = leaders_data['scorers']
                top_points_data, points_query = leaders_data['points']
                top_penalized_data, penalized_query = leaders_data['penalized']
            except Exception as e:
                logger.error(f"Error loading leaders: {e}")
                top_scorers_data, scorers_query = [], ""
                top_points_data, points_query = [], ""
                top_penalized_data, penalized_query = [], ""
            
            is_completed = is_season_completed(season_num)
            season_label = f"{season_num}-{season_num+1} (Completed)" if is_completed else f"{season_num}-{season_num+1} (Current)"
            
            context = {
                'request': request,
                'title': f'Season {season_num} Leaderboards',
                'season': season_num,
                'current_season': season_num,
                'season_label': season_label,
                'available_seasons': AVAILABLE_SEASONS,
                'is_completed': is_completed,
                'scorers': top_scorers_data,
                'scorers_query': scorers_query,
                'points': top_points_data,
                'points_query': points_query,
                'penalized': top_penalized_data,
                'penalized_query': penalized_query,
            }
            
            return render_template("leaders.html", context)
        
        finally:
            session.close()

# ==================== PLAYERS PAGE ====================

@router.get("/players", response_class=HTMLResponse)
async def players(
    request: Request,
    season: int = CURRENT_SEASON,
    position: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Players page
    Shows players for the selected season with searchable and filterable list
    
    NOTE: Uses DeduplicationService to safely handle databases with duplicate player records
    """
    
    # Validate season
    if season not in AVAILABLE_SEASONS:
        season = CURRENT_SEASON
    
    # Query only the selected season's database
    engine = get_engine(season)
    session = Session(engine)
    
    try:
        # Get unique players from the selected season using safe deduplication
        unique_players = DeduplicationService.get_unique_players_in_season(session, season)
        
        # Build player list with stats from PlayerSeason
        players_list = []
        all_positions = set()
        
        for player in unique_players:
            # Get stats for this player in this season
            stmt = select(PlayerSeason).where(
                PlayerSeason.player_id == player.id
            ).where(
                PlayerSeason.season == season
            )
            season_stats = session.exec(stmt).first()
            
            player_data = {
                'id': player.id,
                'name': player.name,
                'position': player.position,
                'jersey_number': player.jersey_number,
                'season': season,
            }
            
            # Add season stats if available
            if season_stats:
                player_data.update({
                    'games_played': season_stats.games_played,
                    'goals': season_stats.goals,
                    'assists': season_stats.assists,
                    'points': season_stats.points,
                })
            
            players_list.append(player_data)
            
            if player.position:
                all_positions.add(player.position)
        
        # Apply filters
        if search:
            players_list = [p for p in players_list if search.lower() in p['name'].lower()]
        
        if position:
            players_list = [p for p in players_list if p['position'] and p['position'].upper() == position.upper()]
        
        players_list.sort(key=lambda p: p['name'])
        
        positions = sorted(list(all_positions))
        
        # Build query string for learning
        query_parts = [f"-- Shows all players for Season {season}"]
        query_parts.append("SELECT DISTINCT p.name, p.position, p.jersey_number")
        query_parts.append("FROM players p")
        query_parts.append("LEFT JOIN player_stats ps ON p.id = ps.player_id")
        query_parts.append(f"WHERE ps.season = {season}")
        if search:
            query_parts.append(f"AND p.name LIKE '%{search}%'")
        if position:
            query_parts.append(f"AND p.position = '{position.upper()}'")
        query_parts.append("ORDER BY p.name;")
        
        query_string = "\n".join(query_parts)
        
        context = {
            'request': request,
            'title': f'Season {season} Players - {len(players_list)} Total',
            'players': players_list,
            'positions': positions,
            'selected_position': position,
            'search_term': search,
            'season': season,
            'current_season': season,
            'selected_season': season,
            'available_seasons': AVAILABLE_SEASONS,
            'query_string': query_string,
        }
        
        return render_template("players.html", context)
    
    finally:
        session.close()

# ==================== PLAYER DETAIL PAGE ====================

@router.get("/player/{player_name}", response_class=HTMLResponse)
async def player_detail(
    request: Request,
    player_name: str
):
    """
    Individual player detail page showing career stats across all seasons
    Shows career timeline, season-by-season performance, and analysis
    """
    from urllib.parse import unquote
    player_name = unquote(player_name)  # Handle URL-encoded names
    
    # Create sessions for all seasons
    sessions = {season: Session(get_engine(season)) for season in AVAILABLE_SEASONS}
    
    try:
        # Get comprehensive career stats
        career_data = AnalysisService.get_player_career_stats(sessions, player_name)
        
        if not career_data or 'all_seasons' not in career_data:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
        
        # Generate analysis summary
        analysis_html = AnalysisService.generate_player_summary_text(career_data)
        
        # Prepare chart data
        seasons_list = career_data['all_seasons']
        chart_data = {
            'seasons': [f"{s['season']}-{s['season']+1}" for s in seasons_list],
            'points': [s['points'] for s in seasons_list],
            'goals': [s['goals'] for s in seasons_list],
            'assists': [s['assists'] for s in seasons_list],
            'ppg': [s['ppg'] for s in seasons_list],
            'games': [s['games_played'] for s in seasons_list],
        }
        chart_data_json = json.dumps(chart_data)
        
        # Get player object from any season (for basic info - use deduplication service)
        player = None
        for season, session in sessions.items():
            # Use deduplication service to safely find player by name
            player = DeduplicationService.get_player_by_name_unique(session, player_name)
            if player:
                break
        
        # Build context
        context = {
            'request': request,
            'title': f'{player_name} - Career Stats',
            'player_name': player_name,
            'player': player,
            'career_data': career_data,
            'seasons': seasons_list,
            'analysis_html': analysis_html,
            'chart_data_json': chart_data_json,
            'is_career_page': True,
        }
        
        return render_template("player_detail.html", context)
    finally:
        for s in sessions.values():
            s.close()

# ==================== SEASON ANALYSIS PAGE ====================

@router.get("/predict", response_class=HTMLResponse)
async def predict_page(
    request: Request,
    season: str = str(CURRENT_SEASON),
    sort_by: str = "points"
):
    """
    Season Analysis Dashboard
    Shows player performance analysis for a season (or all seasons) with charts and insights
    """
    # Handle "all" seasons
    if season.lower() == "all" or season == "0":
        # Aggregate data from all seasons
        all_players = {}
        all_overview = {
            'player_count': 0,
            'total_goals': 0,
            'total_assists': 0,
            'total_points': 0,
            'total_pim': 0,
            'avg_ppg': 0.0
        }
        total_points_sum = 0
        total_games = 0
        
        sessions = {s: Session(get_engine(s)) for s in AVAILABLE_SEASONS}
        
        try:
            for season_num, session in sessions.items():
                season_overview = AnalysisService.get_season_overview(session, season_num)
                players_data = AnalysisService.get_top_performers(session, season_num, limit=100)
                
                # Aggregate stats
                all_overview['player_count'] += season_overview.get('player_count', 0)
                all_overview['total_goals'] += season_overview.get('total_goals', 0)
                all_overview['total_assists'] += season_overview.get('total_assists', 0)
                all_overview['total_points'] += season_overview.get('total_points', 0)
                all_overview['total_pim'] += season_overview.get('total_pim', 0)
                
                for p in players_data:
                    name = p['name']
                    if name not in all_players:
                        all_players[name] = {
                            'name': name,
                            'position': p.get('position', '-'),
                            'goals': 0,
                            'assists': 0,
                            'points': 0,
                            'games_played': 0,
                            'ppg': 0.0
                        }
                    all_players[name]['goals'] += p.get('goals', 0)
                    all_players[name]['assists'] += p.get('assists', 0)
                    all_players[name]['points'] += p.get('points', 0)
                    all_players[name]['games_played'] += p.get('games_played', 0)
                    total_points_sum += p.get('points', 0)
                    total_games += p.get('games_played', 0)
                
                session.close()
            
            # Calculate PPG for aggregated players
            players_data = list(all_players.values())
            for p in players_data:
                if p['games_played'] > 0:
                    p['ppg'] = round(p['points'] / p['games_played'], 2)
            
            # Calculate average PPG
            if total_games > 0:
                all_overview['avg_ppg'] = round(total_points_sum / total_games, 2)
            
            # Sort based on query parameter
            sort_options = {
                'points': lambda x: x['points'],
                'ppg': lambda x: x['ppg'],
                'goals': lambda x: x['goals'],
                'assists': lambda x: x['assists'],
                'games': lambda x: x['games_played'],
            }
            
            if sort_by in sort_options:
                players_data = sorted(players_data, key=sort_options[sort_by], reverse=True)
            
            players_data = players_data[:20]  # Top 20
            
            # Prepare data for charts
            chart_data = {
                'names': [p['name'] for p in players_data],
                'points': [p['points'] for p in players_data],
                'goals': [p['goals'] for p in players_data],
                'assists': [p['assists'] for p in players_data],
                'ppg': [p['ppg'] for p in players_data],
            }
            chart_data_json = json.dumps(chart_data)
            
            query_string = """
-- Aggregated statistics across all seasons
SELECT 
    p.name,
    COUNT(DISTINCT ps.season) as seasons_played,
    SUM(ps.games_played) as total_games,
    SUM(ps.goals) as total_goals,
    SUM(ps.assists) as total_assists,
    SUM(ps.points) as total_points,
    ROUND(CAST(SUM(ps.points) AS FLOAT) / SUM(ps.games_played), 2) as career_ppg
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
GROUP BY p.name
ORDER BY SUM(ps.points) DESC
LIMIT 20;
            """.strip()
            
            context = {
                'request': request,
                'title': 'All Seasons Analysis Dashboard',
                'season': 'all',
                'current_season': 'all',
                'season_label': 'Career Stats (All 10 Seasons)',
                'available_seasons': AVAILABLE_SEASONS,
                'season_overview': all_overview,
                'players': players_data,
                'chart_data_json': chart_data_json,
                'current_sort': sort_by,
                'query_string': query_string,
            }
            
            return render_template("predict.html", context)
        finally:
            for s in sessions.values():
                try:
                    s.close()
                except:
                    pass
    else:
        # Single season mode
        try:
            season_num = int(season)
        except (ValueError, TypeError):
            season_num = CURRENT_SEASON
        
        if season_num not in AVAILABLE_SEASONS:
            season_num = CURRENT_SEASON
        
        engine = get_engine(season_num)
        session = Session(engine)
        
        try:
            # Get season overview
            season_overview = AnalysisService.get_season_overview(session, season_num)
            
            # Get top performers with metrics
            players_data = AnalysisService.get_top_performers(session, season_num, limit=20)
            
            # Sort based on query parameter
            sort_options = {
                'points': lambda x: x['points'],
                'ppg': lambda x: x['ppg'],
                'goals': lambda x: x['goals'],
                'assists': lambda x: x['assists'],
                'games': lambda x: x['games_played'],
            }
            
            if sort_by in sort_options:
                players_data = sorted(players_data, key=sort_options[sort_by], reverse=True)
            
            # Prepare data for charts (JSON for JavaScript)
            chart_data = {
                'names': [p['name'] for p in players_data],
                'points': [p['points'] for p in players_data],
                'goals': [p['goals'] for p in players_data],
                'assists': [p['assists'] for p in players_data],
                'ppg': [p['ppg'] for p in players_data],
            }
            chart_data_json = json.dumps(chart_data)
            
            query_string = f"""
SELECT 
    p.id,
    p.name,
    p.position,
    ps.games_played,
    ps.goals,
    ps.assists,
    ps.points,
    ROUND(CAST(ps.points AS FLOAT) / ps.games_played, 2) as ppg
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE ps.season = {season_num}
ORDER BY ps.points DESC
LIMIT 20;
            """.strip()
            
            # Determine if season is completed
            is_completed = is_season_completed(season_num)
            season_label = f"{season_num}-{season_num+1} (Completed)" if is_completed else f"{season_num}-{season_num+1} (Current)"
            
            context = {
                'request': request,
                'title': f'Season {season_num} Analysis Dashboard',
                'season': season_num,
                'current_season': season_num,
                'season_label': season_label,
                'available_seasons': AVAILABLE_SEASONS,
                'season_overview': season_overview,
                'players': players_data,
                'chart_data_json': chart_data_json,
                'current_sort': sort_by,
                'query_string': query_string,
            }
            
            return render_template("predict.html", context)
        finally:
            session.close()

# ==================== ABOUT DATA PAGE ====================

@router.get("/about-data", response_class=HTMLResponse)
async def about_data(
    request: Request,
    season: str = str(CURRENT_SEASON)
):
    """
    About data page
    Explains data sources and refresh status
    """
    # For about-data, we always get logs from current season database
    # but display info about all seasons
    if season.lower() == "all" or season == "0":
        # Get logs from current season database
        engine = get_engine(CURRENT_SEASON)
        session = Session(engine)
        
        try:
            refresh_logs = session.query(RefreshLog).order_by(RefreshLog.refresh_time.desc()).limit(5).all()
            
            query_string = """
-- Data refresh logs across all seasons
SELECT 
    source_url,
    refresh_time,
    status,
    record_count,
    error_message
FROM refresh_logs
ORDER BY refresh_time DESC
LIMIT 10;
            """.strip()
            
            context = {
                'request': request,
                'title': 'About Our Data - All Seasons',
                'season': 'all',
                'current_season': 'all',
                'available_seasons': AVAILABLE_SEASONS,
                'refresh_logs': refresh_logs,
                'query_string': query_string,
            }
            
            return render_template("about_data.html", context)
        finally:
            session.close()
    else:
        # Single season mode
        try:
            season_num = int(season)
        except (ValueError, TypeError):
            season_num = CURRENT_SEASON
        
        if season_num not in AVAILABLE_SEASONS:
            season_num = CURRENT_SEASON
        
        # Create session for this season
        engine = get_engine(season_num)
        session = Session(engine)
        
        try:
            # Get data source info
            refresh_logs = session.query(RefreshLog).order_by(RefreshLog.refresh_time.desc()).limit(5).all()
        
            query_string = f"""
SELECT 
    source_url,
    refresh_time,
    status,
    record_count,
    error_message
FROM refresh_logs
WHERE season = {season_num}
ORDER BY refresh_time DESC
LIMIT 10;
            """.strip()
            
            context = {
                'request': request,
                'title': 'About Our Data',
                'season': season_num,
                'current_season': season_num,
                'available_seasons': AVAILABLE_SEASONS,
                'refresh_logs': refresh_logs,
                'query_string': query_string,
            }
            
            return render_template("about_data.html", context)
        finally:
            session.close()

# ==================== DATA REFRESH ROUTE (LOCAL DEV ONLY) ====================

@router.get("/admin/refresh-data", response_class=HTMLResponse)
async def refresh_data(
    request: Request,
    season: int = CURRENT_SEASON
):
    """
    Refresh data from source (LOCAL DEVELOPMENT ONLY)
    
    This route should only be available in development mode!
    In production, use scheduled tasks or API endpoints instead.
    """
    import os
    if os.getenv("ENV", "development") != "development":
        raise HTTPException(status_code=403, detail="This endpoint is only available in development")
    
    # Create session for this season
    engine = get_engine(season)
    session = Session(engine)
    
    logger.info("Starting data refresh...")
    
    try:
        # Scrape roster
        roster_data = ErieScraper.scrape_roster()
        
        # Scrape stats
        stats_data = ErieScraper.scrape_stats(season=season)
        
        # Log the refresh
        refresh_log = RefreshLog(
            source_url="OHL Stats Pages",
            status="success",
            record_count=len(roster_data) + len(stats_data),
        )
        session.add(refresh_log)
        session.commit()
        
        logger.info(f"Refresh completed. Scraped {len(roster_data)} roster records and {len(stats_data)} stat records")
        
        context = {
            'request': request,
            'title': 'Data Refresh Complete',
            'season': season,
            'current_season': season,
            'available_seasons': AVAILABLE_SEASONS,
            'roster_count': len(roster_data),
            'stats_count': len(stats_data),
            'status': 'success',
        }
        
        return render_template("about_data.html", context)
        
    except Exception as e:
        logger.error(f"Error during refresh: {e}")
        
        refresh_log = RefreshLog(
            source_url="OHL Stats Pages",
            status="error",
            error_message=str(e),
        )
        session.add(refresh_log)
        session.commit()
        
        # Get refresh logs to display
        refresh_logs = session.query(RefreshLog).order_by(RefreshLog.refresh_time.desc()).limit(5).all()
        
        context = {
            'request': request,
            'title': 'About Our Data',
            'season': season,
            'current_season': season,
            'available_seasons': AVAILABLE_SEASONS,
            'refresh_logs': refresh_logs,
            'error': str(e),
            'status': 'error',
        }
        
        return render_template("about_data.html", context)
    finally:
        session.close()
