import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
from typing import List, Dict, Tuple
import json
import time


class ErieOttersSeasonScraper:
    """Scrape Erie Otters player statistics from CHL website for all seasons"""

    # Map season numbers to years
    # Season 1 = 2000-2001, Season 2 = 2001-2002, ..., Season 25 = 2024-2025, Season 26 = 2025-2026
    SEASON_MAP = {
        1: "2000-2001",
        2: "2001-2002",
        3: "2002-2003",
        4: "2003-2004",
        5: "2004-2005",
        6: "2005-2006",
        7: "2006-2007",
        8: "2007-2008",
        9: "2008-2009",
        10: "2009-2010",
        11: "2010-2011",
        12: "2011-2012",
        13: "2012-2013",
        14: "2013-2014",
        15: "2014-2015",
        16: "2015-2016",
        17: "2016-2017",
        18: "2017-2018",
        19: "2018-2019",
        20: "2019-2020",
        21: "2020-2021",
        22: "2021-2022",
        23: "2022-2023",
        24: "2023-2024",
        25: "2024-2025",
        26: "2025-2026"  # Current season from website
    }

    def __init__(self):
        self.base_url = "https://chl.ca/ohl-otters/stats/players"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def scrape_season(self, season_num: int) -> List[Dict]:
        """Scrape a single season by season number"""
        url = f"{self.base_url}/{season_num}/"
        season_year = self.SEASON_MAP.get(season_num, f"Season {season_num}")
        
        print(f"Scraping season {season_num} ({season_year})...")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players = []
            tables = soup.find_all('table')
            
            if not tables:
                print(f"  ⚠️  No tables found for season {season_num}")
                return players
            
            # Use the first table
            table = tables[0]
            rows = table.find_all('tr')
            
            if len(rows) <= 1:
                print(f"  ⚠️  No player data found for season {season_num}")
                return players
            
            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 8:
                    continue
                
                try:
                    # Get text from each cell
                    cell_texts = [cell.text.strip() for cell in cells]
                    
                    # Only process rows with valid player data
                    if not cell_texts[4]:  # name field empty
                        continue
                    
                    # Extract data - adjust indices based on actual table structure
                    try:
                        gp = int(cell_texts[6]) if len(cell_texts) > 6 and cell_texts[6].isdigit() else 0
                        goals = int(cell_texts[7]) if len(cell_texts) > 7 and cell_texts[7].isdigit() else 0
                        assists = int(cell_texts[8]) if len(cell_texts) > 8 and cell_texts[8].isdigit() else 0
                        points = int(cell_texts[9]) if len(cell_texts) > 9 and cell_texts[9].isdigit() else 0
                        pm = int(cell_texts[10]) if len(cell_texts) > 10 and cell_texts[10].lstrip('-').isdigit() else 0
                        pim = int(cell_texts[11]) if len(cell_texts) > 11 and cell_texts[11].isdigit() else 0
                    except (ValueError, IndexError):
                        continue
                    
                    # Only add if player has stats
                    if gp > 0 or goals > 0 or assists > 0 or points > 0:
                        player_data = {
                            'season': int(season_year.split('-')[0]),
                            'season_label': season_year,
                            'rank': cell_texts[0] if len(cell_texts) > 0 else '',
                            'position': cell_texts[1] if len(cell_texts) > 1 else '',
                            'jersey': cell_texts[2] if len(cell_texts) > 2 else '',
                            'name': cell_texts[4] if len(cell_texts) > 4 else '',
                            'team': cell_texts[5] if len(cell_texts) > 5 else 'ER',
                            'games_played': gp,
                            'goals': goals,
                            'assists': assists,
                            'points': points,
                            'plus_minus': pm,
                            'penalty_minutes': pim,
                        }
                        players.append(player_data)
                
                except Exception as e:
                    continue
            
            print(f"  ✓ Scraped {len(players)} players from season {season_num}")
            return players
        
        except requests.RequestException as e:
            print(f"  ✗ Error fetching season {season_num}: {e}")
            return []

    def scrape_all_seasons(self, seasons: List[int] = None) -> List[Dict]:
        """Scrape multiple seasons"""
        if seasons is None:
            seasons = list(range(1, 27))  # All 26 seasons
        
        all_players = []
        
        for season_num in seasons:
            players = self.scrape_season(season_num)
            all_players.extend(players)
            time.sleep(1)  # Be nice to the server
        
        return all_players

    def save_to_csv(self, players: List[Dict], output_path: str = "data/erie_otters_all_seasons.csv"):
        """Save scraped data to CSV"""
        if not players:
            print("No data to save")
            return
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=players[0].keys())
            writer.writeheader()
            writer.writerows(players)
        
        print(f"\n✅ Saved {len(players)} player records to {output_path}")

    def save_to_json(self, players: List[Dict], output_path: str = "data/erie_otters_all_seasons.json"):
        """Save scraped data to JSON"""
        if not players:
            print("No data to save")
            return
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(players, f, indent=2)
        
        print(f"✅ Saved {len(players)} player records to {output_path}")


if __name__ == "__main__":
    scraper = ErieOttersSeasonScraper()
    
    print("=" * 60)
    print("Erie Otters Multi-Season Scraper (2000-2026)")
    print("=" * 60)
    
    # Scrape specific seasons (user can adjust)
    # For testing, try a few seasons first, then expand
    test_seasons = [26, 25, 24]  # Start with recent seasons
    print(f"\nScraping {len(test_seasons)} seasons for testing...\n")
    
    players = scraper.scrape_all_seasons(test_seasons)
    
    if players:
        scraper.save_to_csv(players)
        scraper.save_to_json(players)
        
        # Summary by season
        print("\n" + "=" * 60)
        print("Summary by Season:")
        print("=" * 60)
        seasons_summary = {}
        for p in players:
            season_label = p['season_label']
            seasons_summary[season_label] = seasons_summary.get(season_label, 0) + 1
        
        for season, count in sorted(seasons_summary.items()):
            print(f"  {season}: {count} players")
        
        print(f"\nTotal: {len(players)} player records")
        
        # Top scorers overall
        print("\n" + "=" * 60)
        print("Top 10 All-Time Scorers (tested seasons):")
        print("=" * 60)
        top_scorers = sorted(players, key=lambda p: p['points'], reverse=True)[:10]
        for i, p in enumerate(top_scorers, 1):
            print(f"  {i}. {p['name']:25} | {p['season_label']:10} | {p['points']:3}pts ({p['goals']}G, {p['assists']}A)")
    else:
        print("Failed to scrape any data")
        print("\nNote: If no data is found, the website may use JavaScript rendering.")
        print("Consider using Selenium or Playwright for dynamic content.")

