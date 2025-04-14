"""Scraper for Toutiao trending content."""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem, fetch_async, logger


class ToutiaoScraper(BaseScraper):
    """Scraper for Toutiao trending content."""

    name = "toutiao"
    display_name = "今日头条"
    
    # Toutiao hot search URL
    HOT_SEARCH_URL = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
    
    async def get_trending(self) -> List[TrendingItem]:
        """Get trending items from Toutiao.
        
        Returns:
            List of trending items
        """
        logger.info(f"Fetching trending content from {self.display_name}")
        
        try:
            # Fetch hot search content
            response_text = await fetch_async(self.HOT_SEARCH_URL)
            
            # Extract JSON data from the response
            json_match = re.search(r'<script>window\._SSR_HYDRATED_DATA=(.*?)</script>', response_text)
            if not json_match:
                logger.error("Failed to extract JSON data from Toutiao response")
                return []
            
            json_str = json_match.group(1).replace('undefined', 'null')
            data = json.loads(json_str)
            
            # Extract trending items
            trending_items = []
            hot_board_data = data.get("ChineseHotBoard", {}).get("hotBoard", {}).get("data", [])
            
            for rank, item in enumerate(hot_board_data, 1):
                # Extract item data
                title = item.get("Title", "")
                url = f"https://www.toutiao.com/search/?keyword={title}"
                hot_value = item.get("HotValue", 0)
                
                # Create trending item
                trending_items.append(
                    TrendingItem(
                        title=title,
                        url=url,
                        rank=rank,
                        score=hot_value,
                        author=None,
                        description=item.get("Abstract", ""),
                        timestamp=datetime.now(),  # Toutiao doesn't provide timestamp for trending items
                        platform=self.name,
                        category="hot_search",
                        extra_data={
                            "label": item.get("Label", ""),
                            "image_url": item.get("Image", {}).get("url", ""),
                            "hot_value_display": item.get("HotValueFormat", ""),
                            "tag": item.get("LabelDesc", ""),
                        }
                    )
                )
            
            return trending_items
            
        except Exception as e:
            logger.error(f"Error fetching trending content from {self.display_name}: {e}")
            return []
