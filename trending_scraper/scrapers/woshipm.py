"""Scraper for WoShiPm (人人都是产品经理) trending content."""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

import aiohttp

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem, logger, fetch_async


class WoShiPmScraper(BaseScraper):
    """Scraper for WoShiPm (人人都是产品经理) trending content."""

    name = "woshipm"
    display_name = "人人都是产品经理"
    
    # API URL for WoShiPm hot list
    API_URL = "https://api.vvhan.com/api/hotlist/woShiPm"
    
    async def get_trending(self) -> List[TrendingItem]:
        """Get trending items from WoShiPm.
        
        Returns:
            List of trending items
        """
        logger.info(f"Fetching trending content from {self.display_name}")
        
        try:
            # 使用fetch_async获取API数据
            response_text = await fetch_async(self.API_URL)
            data = json.loads(response_text)
            
            if not data.get("success"):
                logger.error(f"API返回错误: {data}")
                return []
            
            trending_items = []
            
            # 解析API返回的数据
            items = data.get("data", [])
            update_time_str = data.get("update_time", "")
            
            # 尝试解析更新时间
            update_time = None
            if update_time_str:
                try:
                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"无法解析更新时间: {update_time_str}")
            
            for item in items:
                title = item.get("title", "")
                url = item.get("url", "")
                rank = item.get("index", 0)
                hot = item.get("hot", "")
                
                if not title or not url:
                    continue
                
                # 创建额外数据字典
                extra_data = {
                    "hot_text": hot,
                    "mobile_url": item.get("mobil_url", "")
                }
                
                trending_items.append(
                    TrendingItem(
                        title=title,
                        url=url,
                        rank=rank,
                        score=None,
                        author=None,
                        description="",
                        timestamp=update_time or datetime.now(),
                        platform=self.name,
                        category="hot_article",
                        extra_data=extra_data
                    )
                )
            
            logger.info(f"Successfully extracted {len(trending_items)} trending items from {self.display_name}")
            return trending_items
            
        except Exception as e:
            logger.error(f"Error fetching trending content from {self.display_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
