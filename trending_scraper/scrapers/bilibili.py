"""Scraper for Bilibili trending content."""

import json
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem, fetch_async, logger


class BilibiliScraper(BaseScraper):
    """Scraper for Bilibili trending content."""

    name = "bilibili"
    display_name = "Bilibili"
    
    # API endpoints
    TRENDING_VIDEO_API = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
    TRENDING_TOPICS_API = "https://api.bilibili.com/x/web-interface/search/square?limit=10"
    
    async def get_trending(self) -> List[TrendingItem]:
        """Get trending items from Bilibili.
        
        Returns:
            List of trending items
        """
        logger.info(f"Fetching trending content from {self.display_name}")
        
        try:
            # Fetch trending videos
            trending_videos = await self._get_trending_videos()
            
            # Fetch trending topics
            trending_topics = await self._get_trending_topics()
            
            # Combine results
            return trending_videos + trending_topics
            
        except Exception as e:
            logger.error(f"Error fetching trending content from {self.display_name}: {e}")
            return []
    
    async def _get_trending_videos(self) -> List[TrendingItem]:
        """Get trending videos from Bilibili.
        
        Returns:
            List of trending video items
        """
        try:
            response_text = await fetch_async(self.TRENDING_VIDEO_API)
            data = json.loads(response_text)
            
            if data["code"] != 0:
                logger.error(f"Bilibili API error: {data['message']}")
                return []
            
            trending_items = []
            for rank, item in enumerate(data["data"]["list"], 1):
                trending_items.append(
                    TrendingItem(
                        title=item["title"],
                        url=f"https://www.bilibili.com/video/{item['bvid']}",
                        rank=rank,
                        score=item.get("score"),
                        author=item.get("owner", {}).get("name"),
                        description=item.get("desc"),
                        timestamp=datetime.fromtimestamp(item["pubdate"]) if "pubdate" in item else None,
                        platform=self.name,
                        category="video",
                        extra_data={
                            "play_count": item.get("stat", {}).get("view"),
                            "danmaku_count": item.get("stat", {}).get("danmaku"),
                            "like_count": item.get("stat", {}).get("like"),
                            "duration": item.get("duration"),
                        }
                    )
                )
            
            return trending_items
            
        except Exception as e:
            logger.error(f"Error fetching trending videos from {self.display_name}: {e}")
            return []
    
    async def _get_trending_topics(self) -> List[TrendingItem]:
        """Get trending topics from Bilibili.
        
        Returns:
            List of trending topic items
        """
        try:
            response_text = await fetch_async(self.TRENDING_TOPICS_API)
            data = json.loads(response_text)
            
            if data["code"] != 0:
                logger.error(f"Bilibili API error: {data['message']}")
                return []
            
            trending_items = []
            for rank, item in enumerate(data["data"]["trending"].get("list", []), 1):
                trending_items.append(
                    TrendingItem(
                        title=item["keyword"],
                        url=f"https://search.bilibili.com/all?keyword={item['keyword']}",
                        rank=rank,
                        score=item.get("hot_score"),
                        author=None,
                        description=item.get("show_name"),
                        timestamp=None,
                        platform=self.name,
                        category="topic",
                        extra_data={
                            "icon": item.get("icon"),
                            "topic_type": item.get("type"),
                        }
                    )
                )
            
            return trending_items
            
        except Exception as e:
            logger.error(f"Error fetching trending topics from {self.display_name}: {e}")
            return []
