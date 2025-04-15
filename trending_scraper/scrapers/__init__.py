"""Scrapers for various platforms."""

import abc
import asyncio
from typing import Dict, List, Type

from trending_scraper.utils import TrendingItem, logger


class BaseScraper(abc.ABC):
    """Base class for all scrapers."""

    name: str = "base"
    display_name: str = "Base Scraper"
    
    @abc.abstractmethod
    async def get_trending(self) -> List[TrendingItem]:
        """Get trending items from the platform.
        
        Returns:
            List of trending items
        """
        pass
    
    @classmethod
    def get_scraper_classes(cls) -> Dict[str, Type["BaseScraper"]]:
        """Get all available scraper classes.
        
        Returns:
            Dictionary mapping scraper names to scraper classes
        """
        scrapers = {}
        for scraper_cls in cls.__subclasses__():
            scrapers[scraper_cls.name] = scraper_cls
        return scrapers
    
    @classmethod
    def get_all_scrapers(cls) -> Dict[str, "BaseScraper"]:
        """Get instances of all available scrapers.
        
        Returns:
            Dictionary mapping scraper names to scraper instances
        """
        return {name: scraper_cls() for name, scraper_cls in cls.get_scraper_classes().items()}


# Import all scrapers to register them
from .bilibili import BilibiliScraper
from .toutiao import ToutiaoScraper
from .woshipm import WoShiPmScraper

__all__ = ["BaseScraper", "BilibiliScraper", "ToutiaoScraper", "WoShiPmScraper"]
