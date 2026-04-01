import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
from typing import List, Dict
import json


class ErieOttersScraperScraperWebScraper:
    """Scrape Erie Otters player statistics from CHL website"""

    def __init__(self):
        self.base_url = "https://chl.ca/ohl-otters/stats/players"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def scrape_current_season(self) -> List[Dict]:
        """Scrape current season player stats"""
        url = f"{self.base_url}/14/"  # Season 14/2025-2026
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players = []
            
            # Save HTML for debugging
            # with open('debug.html', 'w') as f:
            #     f.write(soup.prettify())
            
            # Try different table selectors
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables on page")
            
            if not tables:
                print("Warning: Could not find any tables. The site may use JavaScript rendering.")
                print("Trying to find data containers...")
                
                # Try to find any divs that might contain player data
                divs = soup.find_all('div', recursive=True)
                print(f"Found {len(divs)} divs")
                return players
            
            # Use the first table (usually the stats table)
            table = tables[0]
            rows = table.find_all('tr')
            print(f"Found {len(rows)} rows in table")
            
            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 5:
                    continue
                
                try:
                    # Get text from each cell
                    cell_texts = [cell.text.strip() for cell in cells]
                    print(f"Row data: {cell_texts[:8]}")  # Debug: print first 8 columns
                    
                    # Extract data from cells
                    player_data = {
                        'rank': cell_texts[0] if len(cell_texts) > 0 else '',
                        'position': cell_texts[1] if len(cell_texts) > 1 else '',
                        'jersey': cell_texts[2] if len(cell_texts) > 2 else '',
                        'name': cell_texts[4] if len(cell_texts) > 4 else '',
                        'team': cell_texts[5] if len(cell_texts) > 5 else 'ER',
                        'games_played': int(cell_texts[6]) if len(cell_texts) > 6 and cell_texts[6].isdigit() else 0,
                        'goals': int(cell_texts[7]) if len(cell_texts) > 7 and cell_texts[7].isdigit() else 0,
                        'assists': int(cell_texts[8]) if len(cell_texts) > 8 and cell_texts[8].isdigit() else 0,
                        'points': int(cell_texts[9]) if len(cell_texts) > 9 and cell_texts[9].isdigit() else 0,
                        'plus_minus': int(cell_texts[10]) if len(cell_texts) > 10 and cell_texts[10].lstrip('-').isdigit() else 0,
                        'pim': int(cell_texts[11]) if len(cell_texts) > 11 and cell_texts[11].isdigit() else 0,
                    }
                    
                    if player_data['name']:  # Only add if name is not empty
                        players.append(player_data)
                
                except (ValueError, IndexError) as e:
                    pass  # Skip rows with bad data
                    continue
            
            print(f"Scraped {len(players)} players")
            return players
        
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return []

    def save_to_csv(self, players: List[Dict], output_path: str = "data/erie_otters_2025_2026.csv"):
        """Save scraped data to CSV"""
        if not players:
            print("No data to save")
            return
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=players[0].keys())
            writer.writeheader()
            writer.writerows(players)
        
        print(f"Saved {len(players)} players to {output_path}")

    def save_to_json(self, players: List[Dict], output_path: str = "data/erie_otters_2025_2026.json"):
        """Save scraped data to JSON"""
        if not players:
            print("No data to save")
            return
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(players, f, indent=2)
        
        print(f"Saved {len(players)} players to {output_path}")


if __name__ == "__main__":
    scraper = ErieOttersScraperScraperWebScraper()
    
    print("Scraping Erie Otters player statistics...")
    players = scraper.scrape_current_season()
    
    if players:
        scraper.save_to_csv(players)
        scraper.save_to_json(players)
        print("\nTop 5 scorers:")
        for player in sorted(players, key=lambda p: p['points'], reverse=True)[:5]:
            print(f"  {player['name']}: {player['points']} points ({player['goals']}G, {player['assists']}A)")
    else:
        print("Failed to scrape data")
