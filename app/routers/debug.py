"""
Debug and diagnostic routes for database health and duplicate detection
Access: /debug/audit, /debug/audit/details, /debug/cleanup (admin)
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from app.database import get_engine, AVAILABLE_SEASONS
from app.services.deduplication import DeduplicationService
from app.services.database_cleanup import DatabaseCleanup
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

router = APIRouter(prefix="/debug", tags=["debug"])

# Setup Jinja2 environment for debug templates
APP_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = APP_DIR / "templates"

if TEMPLATES_DIR.exists():
    jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        cache_size=0
    )
else:
    jinja_env = None


@router.get("/audit", response_class=JSONResponse)
async def audit_duplicates():
    """
    Audit all season databases for duplicate player records.
    
    Returns JSON with summary of duplicates found in each season.
    
    Response:
    {
        "total_seasons": 10,
        "total_duplicates_across_all_seasons": 150,
        "seasons": [
            {
                "season": 2019,
                "total_players": 33,
                "unique_players": 23,
                "duplicate_records": 10,
                "duplicated_names": ["Brendan Brisson", "Jack Perbix", ...]
            },
            ...
        ]
    }
    """
    audit_results = {
        "total_seasons": len(AVAILABLE_SEASONS),
        "seasons": [],
        "total_duplicates_across_all_seasons": 0,
    }
    
    for season in AVAILABLE_SEASONS:
        engine = get_engine(season)
        session = Session(engine)
        
        try:
            total, unique, duplicates = DeduplicationService.count_duplicates(session)
            dup_dict = DeduplicationService.find_duplicate_players(session)
            duplicated_names = list(dup_dict.keys())
            
            season_audit = {
                "season": season,
                "total_players": total,
                "unique_players": unique,
                "duplicate_records": duplicates,
                "duplicated_names": duplicated_names
            }
            
            audit_results["seasons"].append(season_audit)
            audit_results["total_duplicates_across_all_seasons"] += duplicates
        
        finally:
            session.close()
    
    return audit_results


@router.get("/audit/details", response_class=JSONResponse)
async def audit_details(season: int = Query(2019)):
    """
    Get detailed duplicate information for a specific season.
    
    Query Parameters:
        season: Season year (default: 2019)
    
    Returns:
    {
        "season": 2019,
        "stats": {
            "total_players": 33,
            "unique_players": 23,
            "duplicate_records": 10
        },
        "duplicates": {
            "Brendan Brisson": {
                "count": 3,
                "player_ids": [1, 4, 14],
                "stats_identical": true
            },
            ...
        }
    }
    """
    if season not in AVAILABLE_SEASONS:
        raise HTTPException(status_code=400, detail=f"Invalid season {season}")
    
    engine = get_engine(season)
    session = Session(engine)
    
    try:
        # Get overall stats
        total, unique, duplicates = DeduplicationService.count_duplicates(session)
        
        # Get detailed duplicate info
        dup_dict = DeduplicationService.find_duplicate_players(session)
        
        duplicates_detailed = {}
        for player_name, ids in dup_dict.items():
            stats_identical = DeduplicationService.validate_duplicate_stats_are_identical(
                session, player_name
            )
            
            duplicates_detailed[player_name] = {
                "count": len(ids),
                "player_ids": sorted(ids),
                "stats_identical": stats_identical,
                "keep_id": min(ids),  # The one we'd keep during cleanup
                "delete_ids": sorted([id for id in ids if id != min(ids)])
            }
        
        return {
            "season": season,
            "stats": {
                "total_players": total,
                "unique_players": unique,
                "duplicate_records": duplicates
            },
            "duplicates": duplicates_detailed
        }
    
    finally:
        session.close()


@router.post("/cleanup/dry-run", response_class=JSONResponse)
async def cleanup_dry_run(season: int = Query(None)):
    """
    Simulate cleanup without actually deleting anything.
    
    Query Parameters:
        season: Optional season year. If not provided, all seasons are checked.
    
    Returns cleanup plan (what would be deleted)
    """
    if season is not None:
        if season not in AVAILABLE_SEASONS:
            raise HTTPException(status_code=400, detail=f"Invalid season {season}")
        
        result = DatabaseCleanup.cleanup_season(season, dry_run=True)
        return result
    else:
        result = DatabaseCleanup.cleanup_all_seasons(dry_run=True)
        return result


@router.post("/cleanup/execute", response_class=JSONResponse)
async def cleanup_execute(season: int = Query(None), confirm: bool = Query(False)):
    """
    Actually execute cleanup and delete duplicate records.
    
    ⚠️  DESTRUCTIVE OPERATION - Deletes data from database
    
    Query Parameters:
        season: Optional season year. If not provided, all seasons are cleaned.
        confirm: Must be True to actually execute cleanup
    
    Returns cleanup results (what was deleted)
    """
    if not confirm:
        return {
            "status": "aborted",
            "message": "Must set confirm=true to execute cleanup"
        }
    
    if season is not None:
        if season not in AVAILABLE_SEASONS:
            raise HTTPException(status_code=400, detail=f"Invalid season {season}")
        
        result = DatabaseCleanup.cleanup_season(season, dry_run=False)
        return result
    else:
        result = DatabaseCleanup.cleanup_all_seasons(dry_run=False)
        return result


@router.get("/verify", response_class=JSONResponse)
async def verify_integrity(season: int = Query(2019)):
    """
    Verify data integrity of a season database.
    
    Checks for:
    - Duplicate player names
    - Inconsistent stats for duplicates
    - Data anomalies
    
    Query Parameters:
        season: Season year (default: 2019)
    
    Returns detailed integrity report
    """
    if season not in AVAILABLE_SEASONS:
        raise HTTPException(status_code=400, detail=f"Invalid season {season}")
    
    engine = get_engine(season)
    session = Session(engine)
    
    try:
        result = DatabaseCleanup.verify_data_integrity_season(session)
        return {
            "season": season,
            "integrity_ok": not result['duplicates_found'],
            **result
        }
    finally:
        session.close()


@router.get("/status", response_class=JSONResponse)
async def status_check():
    """
    Quick health check - shows if any duplicates exist across all databases.
    
    Returns:
    {
        "healthy": false,
        "seasons_with_duplicates": 10,
        "total_duplicate_records": 75,
        "recommendation": "Run /debug/cleanup/dry-run to see detailed cleanup plan"
    }
    """
    all_duplicates = 0
    seasons_with_issues = 0
    
    for season in AVAILABLE_SEASONS:
        engine = get_engine(season)
        session = Session(engine)
        
        try:
            _, _, dup_count = DeduplicationService.count_duplicates(session)
            if dup_count > 0:
                seasons_with_issues += 1
                all_duplicates += dup_count
        finally:
            session.close()
    
    healthy = all_duplicates == 0
    
    return {
        "healthy": healthy,
        "seasons_with_duplicates": seasons_with_issues,
        "total_duplicate_records": all_duplicates,
        "recommendation": (
            "Database is clean ✅" if healthy 
            else "Run /debug/cleanup/dry-run to see cleanup plan"
        )
    }


@router.get("/summary", response_class=HTMLResponse)
async def summary_html():
    """
    HTML summary page showing database health and duplicate counts.
    """
    audit_result = await audit_duplicates()
    status = await status_check()
    
    # Build HTML response
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Audit Summary</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .header {
                background: #00205B;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .status-healthy { color: #2ecc71; }
            .status-unhealthy { color: #e74c3c; }
            .season-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .season-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            .season-card h3 {
                margin-top: 0;
                color: #00205B;
            }
            .stat-row {
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
                border-bottom: 1px solid #f0f0f0;
            }
            .stat-row:last-child {
                border-bottom: none;
            }
            .stat-value {
                font-weight: bold;
                color: #FFD700;
            }
            .status-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
            }
            .status-issue {
                background: #ffe6e6;
                color: #c0392b;
            }
            .status-ok {
                background: #e6ffe6;
                color: #27ae60;
            }
            .actions {
                margin-top: 20px;
                padding: 15px;
                background: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            .action-button {
                display: inline-block;
                margin: 5px 5px 5px 0;
                padding: 8px 12px;
                background: #00205B;
                color: white;
                border-radius: 4px;
                text-decoration: none;
                font-size: 14px;
            }
            .action-button:hover {
                background: #FFD700;
                color: #00205B;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Erie Otters Database Audit</h1>
            <div style="margin-top: 10px;">
                <strong>Status:</strong> 
    """
    
    if status['healthy']:
        html += '<span class="status-healthy">✅ HEALTHY</span>'
    else:
        html += f'<span class="status-unhealthy">⚠️ {status["total_duplicate_records"]} duplicate records found</span>'
    
    html += f"""
            </div>
        </div>
        
        <div class="season-grid">
    """
    
    for season_info in audit_result['seasons']:
        season = season_info['season']
        total = season_info['total_players']
        unique = season_info['unique_players']
        dups = season_info['duplicate_records']
        
        has_issues = dups > 0
        badge_class = "status-issue" if has_issues else "status-ok"
        
        html += f"""
            <div class="season-card">
                <h3>Season {season}</h3>
                <span class="status-badge {badge_class}">
                    {"Duplicates found" if has_issues else "Clean"}
                </span>
                <div class="stat-row">
                    <span>Total Records:</span>
                    <span class="stat-value">{total}</span>
                </div>
                <div class="stat-row">
                    <span>Unique Players:</span>
                    <span class="stat-value">{unique}</span>
                </div>
                <div class="stat-row">
                    <span>Duplicates:</span>
                    <span class="stat-value">{dups}</span>
                </div>
        """
        
        if dups > 0:
            dup_names = season_info['duplicated_names']
            html += f"""
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #f0f0f0;">
                    <p style="margin: 5px 0; font-size: 12px; color: #666;">
                        {len(dup_names)} names with duplicates
                    </p>
                </div>
            """
        
        html += """
            </div>
        """
    
    html += """
        </div>
        
        <div class="actions">
            <h3>Available Actions</h3>
            <a href="/debug/audit" class="action-button">📊 Full Audit (JSON)</a>
            <a href="/debug/audit/details?season=2019" class="action-button">🔎 Detailed Report (2019)</a>
            <a href="/debug/verify?season=2019" class="action-button">✓ Verify Integrity (2019)</a>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; border: 1px solid #ffc107;">
            <strong>⚠️ Cleanup Actions:</strong>
            <p>To clean up duplicates, use POST requests:</p>
            <code style="display: block; margin: 10px 0; padding: 10px; background: white; border-radius: 4px;">
                POST /debug/cleanup/dry-run
            </code>
            <code style="display: block; margin: 10px 0; padding: 10px; background: white; border-radius: 4px;">
                POST /debug/cleanup/execute?confirm=true
            </code>
        </div>
    </body>
    </html>
    """
    
    return html
