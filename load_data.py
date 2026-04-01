#!/usr/bin/env python3
"""
Script to load Erie Otters real data from CSV files into the database
"""

import csv
from pathlib import Path
from datetime import datetime
from sqlmodel import Session, select
from models import engine, Team, Player, PlayerStats, TeamStats, create_db_and_tables


def load_players_from_csv(csv_path: str = "data/erie_otters_2025_2026.csv"):
    """Load player stats from CSV file"""
    create_db_and_tables()
    
    with Session(engine) as session:
        # First, create/get the Erie Otters team
        erie_team = session.exec(
            select(Team).where(Team.name == "Erie Otters")
        ).first()
        
        if not erie_team:
            erie_team = Team(
                name="Erie Otters",
                city="Erie",
                founded_year=2007,
                league="OHL"
            )
            session.add(erie_team)
            session.commit()
            print(f"Created team: Erie Otters (ID: {erie_team.team_id})")
        
        # Load players
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            added_count = 0
            
            for row in reader:
                # Check if player exists
                player = session.exec(
                    select(Player).where(
                        (Player.first_name == row['first_name']) &
                        (Player.last_name == row['last_name'])
                    )
                ).first()
                
                if not player:
                    player = Player(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        birth_year=1999,  # Placeholder
                        position=row['position'],
                        draft_year=None
                    )
                    session.add(player)
                    session.commit()
                    added_count += 1
                
                # Add/update player stats
                stat = session.exec(
                    select(PlayerStats).where(
                        (PlayerStats.player_id == player.player_id) &
                        (PlayerStats.season == int(row['season']))
                    )
                ).first()
                
                if not stat:
                    stat = PlayerStats(
                        player_id=player.player_id,
                        season=int(row['season']),
                        games_played=int(row['games_played']),
                        goals=int(row['goals']),
                        assists=int(row['assists']),
                        points=int(row['points']),
                        plus_minus=int(row['plus_minus']),
                        penalty_minutes=int(row['penalty_minutes'])
                    )
                    session.add(stat)
                    session.commit()
            
            print(f"Loaded {added_count} new players")
            all_stats = session.exec(select(PlayerStats)).all()
            print(f"Total player stats records: {len(all_stats)}")


def load_team_stats_from_csv(csv_path: str = "data/erie_otters_team_stats.csv"):
    """Load team stats from CSV file"""
    
    with Session(engine) as session:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                team = session.exec(
                    select(Team).where(Team.name == "Erie Otters")
                ).first()
                
                if team:
                    stat = TeamStats(
                        team_id=team.team_id,
                        season=int(row['season']),
                        wins=int(row['wins']),
                        losses=int(row['losses']),
                        ot_losses=int(row['ot_losses']),
                        goals_for=int(row['goals_for']),
                        goals_against=int(row['goals_against']),
                        power_play_pct=float(row['power_play_pct']),
                        penalty_kill_pct=float(row['penalty_kill_pct'])
                    )
                    session.add(stat)
                    session.commit()
            
            print(f"Loaded team stats for Erie Otters")


if __name__ == "__main__":
    print("Loading Erie Otters data into database...")
    load_players_from_csv()
    load_team_stats_from_csv()
    print("✅ Database loaded successfully!")
