"""
Services package - Business logic for stats, scraping, and predictions
"""

from .stats_service import StatsService
from .scraper import ErieScraper
from .predictor import PredictorService

__all__ = ['StatsService', 'ErieScraper', 'PredictorService']
