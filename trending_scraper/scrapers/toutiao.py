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
            
            # 尝试多种可能的JSON数据提取模式
            json_patterns = [
                r'<script>window\._SSR_HYDRATED_DATA=(.*?)</script>',
                r'<script id="RENDER_DATA" type="application/json">(.*?)</script>',
                r'window\._SSR_HYDRATED_DATA\s*=\s*({.*?});\s*</script>'
            ]
            
            data = None
            for pattern in json_patterns:
                json_match = re.search(pattern, response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).replace('undefined', 'null')
                    try:
                        # 某些情况下可能需要URL解码
                        if pattern.find('RENDER_DATA') > -1:
                            import urllib.parse
                            json_str = urllib.parse.unquote(json_str)
                        data = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        continue
            
            if not data:
                # 如果无法提取JSON数据，尝试直接从HTML解析
                soup = BeautifulSoup(response_text, 'html.parser')
                trending_items = []
                
                # 查找热搜列表元素
                hot_items = soup.select('.hot-board-item') or soup.select('.hot-list-item')
                
                if hot_items:
                    for rank, item in enumerate(hot_items[:20], 1):
                        title_elem = item.select_one('.title') or item.select_one('.hot-item-title')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        url_elem = item.select_one('a')
                        url = f"https://www.toutiao.com{url_elem['href']}" if url_elem and url_elem.has_attr('href') else f"https://www.toutiao.com/search/?keyword={title}"
                        
                        score_elem = item.select_one('.hot-value') or item.select_one('.hot-item-score')
                        score = score_elem.get_text(strip=True).replace('万', '0000') if score_elem else None
                        try:
                            score = float(re.sub(r'[^\d.]', '', score)) if score else None
                        except ValueError:
                            score = None
                            
                        desc_elem = item.select_one('.abstract') or item.select_one('.hot-item-desc')
                        description = desc_elem.get_text(strip=True) if desc_elem else None
                        
                        trending_items.append(
                            TrendingItem(
                                title=title,
                                url=url,
                                rank=rank,
                                score=score,
                                author=None,
                                description=description,
                                timestamp=datetime.now(),
                                platform=self.name,
                                category="hot_search",
                                extra_data={}
                            )
                        )
                    
                    return trending_items
            
            # 如果成功提取到JSON数据，尝试多种可能的数据结构
            trending_items = []
            
            # 尝试原始数据结构
            hot_board_data = data.get("ChineseHotBoard", {}).get("hotBoard", {}).get("data", [])
            
            # 如果原始结构不存在，尝试其他可能的结构
            if not hot_board_data:
                # 尝试查找任何包含热搜数据的键
                for key, value in data.items():
                    if isinstance(value, dict) and ('hotBoard' in value or 'hot_board' in value or 'hot_list' in value):
                        hot_board_data = value.get('hotBoard', {}).get('data', []) or value.get('hot_board', []) or value.get('hot_list', [])
                        break
                    
                    # 递归查找一级深度
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, dict) and ('hotBoard' in subvalue or 'hot_board' in subvalue or 'hot_list' in subvalue):
                                hot_board_data = subvalue.get('hotBoard', {}).get('data', []) or subvalue.get('hot_board', []) or subvalue.get('hot_list', [])
                                break
            
            # 如果仍然找不到数据，返回空列表
            if not hot_board_data:
                logger.error("Could not find hot board data in Toutiao response")
                return []
            
            for rank, item in enumerate(hot_board_data[:20], 1):
                # 尝试多种可能的字段名
                title = item.get("Title", "") or item.get("title", "") or item.get("content", "")
                url = item.get("url", "") or f"https://www.toutiao.com/search/?keyword={title}"
                if not url.startswith("http"):
                    url = f"https://www.toutiao.com{url}"
                    
                hot_value = item.get("HotValue", 0) or item.get("hot_value", 0) or item.get("score", 0)
                description = item.get("Abstract", "") or item.get("abstract", "") or item.get("description", "")
                
                # 创建趋势项
                trending_items.append(
                    TrendingItem(
                        title=title,
                        url=url,
                        rank=rank,
                        score=float(hot_value) if hot_value else None,
                        author=None,
                        description=description,
                        timestamp=datetime.now(),  # 今日头条不提供热搜项的时间戳
                        platform=self.name,
                        category="hot_search",
                        extra_data={
                            "label": item.get("Label", "") or item.get("label", ""),
                            "image_url": item.get("Image", {}).get("url", "") if isinstance(item.get("Image"), dict) else item.get("image_url", ""),
                            "hot_value_display": item.get("HotValueFormat", "") or item.get("hot_value_format", ""),
                            "tag": item.get("LabelDesc", "") or item.get("label_desc", ""),
                        }
                    )
                )
            
            return trending_items
            
        except Exception as e:
            logger.error(f"Error fetching trending content from {self.display_name}: {e}")
            return []
