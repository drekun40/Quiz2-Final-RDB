"""
Web scraper for Erie Otters stats
Fetches and parses player statistics from CHL website
Supports both static (BeautifulSoup) and dynamic (Selenium) scraping
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

# Try to import Selenium - optional for advanced scraping
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - install with: pip install selenium webdriver-manager")

class ErieScraper:
    """
    Scraper for Erie Otters statistics
    Handles fetching and parsing player data from the web
    
    Methods:
    - scrape_stats_live(): Uses Selenium for JavaScript-heavy sites (recommended)
    - scrape_stats(): Uses BeautifulSoup (static HTML only)
    - scrape_roster(): Gets player roster info
    """
    
    # URLs - updated for actual CHL stats page
    BASE_URL = "https://chl.ca"
    ERIE_STATS_URL = f"{BASE_URL}/ohl-otters/stats/players/14/"  # Team ID: 14 for Erie Otters
    
    @staticmethod
    def scrape_stats_live(season: int = 2026, team_id: int = 14, headless: bool = True) -> List[Dict]:
        """
        Scrape player statistics using Selenium for JavaScript-heavy sites
        This is the recommended method for real CHL data
        
        Args:
            season: The season year to scrape (e.g., 2026)
            team_id: CHL team ID (14 for Erie Otters)
            headless: Run browser in headless mode (no GUI)
            
        Returns:
            List of player statistics dictionaries
            
        Requires:
            pip install selenium webdriver-manager
        """
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not available! Install with: pip install selenium webdriver-manager")
            return []
        
        driver = None
        try:
            logger.info("🌐 Starting Selenium browser for dynamic content...")
            
            # Setup Chrome options
            chrome_options = ChromeOptions()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            stats_url = f"{ErieScraper.BASE_URL}/ohl-otters/stats/players/{team_id}/"
            logger.info(f"📄 Loading: {stats_url}")
            driver.get(stats_url)
            
            # Wait for table to load
            logger.info("⏳ Waiting for stats table to load...")
            wait = WebDriverWait(driver, 15)
            
            try:
                # Wait for table body to appear
                wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "tbody")))
                time.sleep(2)  # Additional wait for rendering
                logger.info("✓ Table loaded!")
            except Exception as e:
                logger.warning(f"Timeout waiting for table: {e}")
                # Continue anyway - page might be loaded even if selector didn't match
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            stats = []
            
            # Find stats table
            table = soup.find('table')
            if not table:
                logger.warning("❌ No stats table found on page")
                return []
            
            tbody = table.find('tbody')
            rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
            
            if not rows:
                logger.warning("❌ No data rows found in table")
                return []
            
            logger.info(f"📊 Found {len(rows)} player rows")
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_all('td')
                    if len(cells) < 7:
                        continue
                    
                    # Extract text from cells
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # CHL Website column positions:
                    # 0:Rank, 1:Pos, 2:Jersey, 3:Inactive, 4:Rookie, 5:Name, 6:Team, 
                    # 7:GP, 8:G, 9:A, 10:PTS, 11:+/-, 12:PIM, 13+:advanced stats
                    
                    if len(cell_texts) < 13:
                        logger.debug(f"  Row {row_idx}: insufficient columns ({len(cell_texts)})")
                        continue
                    
                    # Extract key data from correct positions
                    name = cell_texts[5]  # Player name
                    
                    # Safe integer parsing
                    def safe_int(text, default=0):
                        if not text:
                            return default
                        try:
                            clean = text.replace('+', '').replace('-', '')
                            val = int(clean) if clean else default
                            # Add back minus sign if negative
                            if text.strip().startswith('-') and '-' in text:
                                val = -abs(val)
                            return val
                        except ValueError:
                            return default
                    
                    # Parse stats from correct columns
                    gp = safe_int(cell_texts[7], 0)  # Games Played
                    goals = safe_int(cell_texts[8], 0)  # Goals
                    assists = safe_int(cell_texts[9], 0)  # Assists
                    points = safe_int(cell_texts[10], 0)  # Points
                    plus_minus = safe_int(cell_texts[11], 0)  # +/-
                    pim = safe_int(cell_texts[12], 0)  # PIM
                    
                    # Skip if no name or no GP
                    if not name or gp == 0:
                        continue
                    
                    player_data = {
                        'name': name.strip(),
                        'games_played': gp,
                        'goals': goals,
                        'assists': assists,
                        'points': points,
                        'penalty_minutes': pim,
                        'plus_minus': plus_minus,
                        'season': season,
                        'source': stats_url,
                        'scraped_at': datetime.utcnow()
                    }
                    
                    stats.append(player_data)
                    logger.debug(f"  ✓ {name}: {gp}GP {goals}G {assists}A {points}Pts")
                    
                except Exception as e:
                    logger.warning(f"  Row {row_idx}: Error - {e}")
                    continue
            
            logger.info(f"\n✅ Successfully scraped {len(stats)} players!\n")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Selenium scraping error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
            
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.debug("✓ Browser closed")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
    
        """
        Scrape player roster from CHL website
        
        Returns:
            List of player dictionaries with basic info
            
        Note:
            The CHL website uses dynamic JavaScript loading.
            For production, consider using:
            - Selenium or Playwright for JavaScript rendering
            - CHL's hidden API endpoints if available
            - Direct data extraction if available
        """
        try:
            logger.info(f"Scraping roster from {ErieScraper.ERIE_STATS_URL}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(ErieScraper.ERIE_STATS_URL, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            players = []
            
            # CHL website structure - look for player rows in tables
            # Try multiple possible selectors as the site structure may vary
            player_rows = soup.select('table tbody tr')
            
            if not player_rows:
                # Fallback: try divs with player class
                player_rows = soup.select('[data-player-id*="-"]')
                logger.debug(f"Fallback: Found {len(player_rows)} data-player elements")
            
            for row in player_rows:
                try:
                    # Try to extract data from various possible structures
                    cells = row.find_all('td')
                    
                    if len(cells) < 3:
                        continue
                    
                    # Common structure: #, Name, Position, ...
                    number_text = cells[0].get_text(strip=True)
                    name = cells[1].get_text(strip=True)
                    position = cells[2].get_text(strip=True) if len(cells) > 2 else "UNK"
                    
                    # Clean and validate
                    if not name or not position:
                        continue
                    
                    try:
                        jersey = int(number_text) if number_text.isdigit() else None
                    except (ValueError, AttributeError):
                        jersey = None
                    
                    players.append({
                        'name': name.strip(),
                        'jersey_number': jersey,
                        'position': position.strip().upper(),
                        'source': ErieScraper.ERIE_STATS_URL,
                        'scraped_at': datetime.utcnow()
                    })
                    logger.debug(f"Found player: {name} ({position})")
                    
                except (IndexError, ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse row: {e}")
                    continue
            
            logger.info(f"Scraped {len(players)} players from roster")
            return players
            
        except requests.RequestException as e:
            logger.error(f"Failed to scrape roster: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping roster: {e}")
            return []

    @staticmethod
    def scrape_stats(season: int = 2026, team_id: int = 14) -> List[Dict]:
        """
        Scrape player statistics for a specific season
        
        Args:
            season: The season year to scrape (e.g., 2026, 2025)
            team_id: CHL team ID (14 for Erie Otters)
            
        Returns:
            List of player statistics dictionaries
            
        Note:
            The CHL website uses JavaScript to load player stats tables dynamically.
            For production use, consider:
            1. Using Selenium/Playwright for JavaScript rendering
            2. Finding CHL's API endpoints
            3. Using a service like ScrapingBee that handles JavaScript
            4. Parsing JSON data embedded in page scripts
            
            Current columns on CHL site:
            - # (jersey number)
            - Player Name
            - GP (games played)
            - G (goals)
            - A (assists)
            - Pts (points)
            - PIM (penalty minutes)
            - +/- (plus/minus)
        """
        try:
            # CHL stats URL for Erie Otters (team_id=14)
            stats_url = f"{ErieScraper.BASE_URL}/ohl-otters/stats/players/{team_id}/"
            logger.info(f"Scraping stats from {stats_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(stats_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stats = []
            
            # Look for stats table - try multiple possible structures
            table = soup.find('table')
            if not table:
                logger.warning(f"No stats table found on {stats_url}")
                logger.info("Note: CHL website uses JavaScript. For reliable scraping, use Selenium/Playwright.")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                logger.warning("Stats table found but no tbody element")
                rows = table.find_all('tr')[1:]  # Try all rows, skip header
            else:
                rows = tbody.find_all('tr')
            
            if not rows:
                logger.warning("No data rows found in stats table")
                return []
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_all('td')
                    if len(cells) < 7:
                        logger.debug(f"Row {row_idx}: insufficient cells ({len(cells)}), skipping")
                        continue
                    
                    # Parse each stat - be flexible with column positions
                    # Try to extract: Jersey, Name, GP, G, A, Pts, PIM, +/-
                    
                    cell_values = [cell.get_text(strip=True) for cell in cells]
                    
                    # Find name (usually has non-numeric start, or look for a link)
                    name = None
                    for i, cell in enumerate(cells):
                        link = cell.find('a')
                        if link:
                            name = link.get_text(strip=True)
                            break
                    
                    if not name:
                        # Fallback: assume second column is name
                        name = cell_values[1] if len(cell_values) > 1 else None
                    
                    if not name:
                        logger.debug(f"Row {row_idx}: couldn't extract player name")
                        continue
                    
                    # Extract stats - try to parse numerics
                    def safe_int(text, default=0):
                        try:
                            return int(text.replace('+', '').replace('-', '') or default) if text else default
                        except ValueError:
                            return default
                    
                    # Common structure: [jersey, name, gp, g, a, pts, pim, +/-]
                    jersey = safe_int(cell_values[0]) if cell_values else None
                    gp = safe_int(cell_values[2]) if len(cell_values) > 2 else 0
                    goals = safe_int(cell_values[3]) if len(cell_values) > 3 else 0
                    assists = safe_int(cell_values[4]) if len(cell_values) > 4 else 0
                    points = safe_int(cell_values[5]) if len(cell_values) > 5 else 0
                    pim = safe_int(cell_values[6]) if len(cell_values) > 6 else 0
                    plus_minus = safe_int(cell_values[7]) if len(cell_values) > 7 else 0
                    
                    if gp == 0:
                        logger.debug(f"Row {row_idx} ({name}): games_played=0, skipping")
                        continue
                    
                    stats.append({
                        'name': name,
                        'games_played': gp,
                        'goals': goals,
                        'assists': assists,
                        'points': points,
                        'penalty_minutes': pim,
                        'plus_minus': plus_minus,
                        'season': season,
                        'source': stats_url,
                        'scraped_at': datetime.utcnow()
                    })
                    logger.debug(f"Parsed: {name} - {gp}GP {goals}G {assists}A {points}Pts")
                    
                except Exception as e:
                    logger.warning(f"Row {row_idx}: Failed to parse - {e}")
                    continue
            
            logger.info(f"Scraped stats for {len(stats)} players from {stats_url}")
            return stats
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping stats from {stats_url}")
            return []
        except requests.RequestException as e:
            logger.error(f"Failed to scrape stats: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping stats: {e}")
            return []

    @staticmethod
    def fetch_player_details(player_name: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific player
        
        Args:
            player_name: Name of the player to look up
            
        Returns:
            Dictionary with player details or None if not found
        """
        # This could search the OHL stats page or other sources
        # Implementation depends on available APIs or pages
        logger.info(f"Looking up details for {player_name}")
        
        # Placeholder implementation
        return {
            'name': player_name,
            'looked_up_at': datetime.utcnow()
        }
