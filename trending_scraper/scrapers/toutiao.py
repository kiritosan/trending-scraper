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
    
    # 今日头条热搜URL列表 - 按优先级排序
    HOT_SEARCH_URLS = [
        "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
        "https://www.toutiao.com/toutiao/trending_board/",
        "https://www.toutiao.com/api/pc/hot_gallery/",
        "https://www.toutiao.com/api/pc/feed/",
        "https://www.toutiao.com/"  # 主页作为最后的备选
    ]
    
    async def get_trending(self) -> List[TrendingItem]:
        """Get trending items from Toutiao.
        
        Returns:
            List of trending items
        """
        logger.info(f"Fetching trending content from {self.display_name}")
        
        # 通用请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.toutiao.com/",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        trending_items = []
        
        # 尝试所有可能的URL
        for url in self.HOT_SEARCH_URLS:
            try:
                logger.info(f"Trying URL: {url}")
                response_text = await fetch_async(url, headers=headers)
                
                # 尝试从响应中提取数据
                items = await self._extract_data_from_response(response_text, url)
                if items:
                    trending_items = items
                    logger.info(f"Successfully extracted {len(items)} items from {url}")
                    break
            except Exception as e:
                logger.warning(f"Failed to fetch data from {url}: {e}")
                continue
        
        if not trending_items:
            logger.error("Failed to extract trending data from all URLs")
            
        return trending_items
    
    async def _extract_data_from_response(self, response_text: str, url: str) -> List[TrendingItem]:
        """从响应中提取数据。
        
        Args:
            response_text: 响应文本
            url: 请求的URL
            
        Returns:
            提取的趋势项列表
        """
        trending_items = []
        
        # 1. 尝试从JSON中提取数据
        json_data = self._extract_json_from_html(response_text)
        if json_data:
            items = self._extract_items_from_json(json_data)
            if items:
                return items
        
        # 2. 尝试从HTML中提取数据
        items = self._extract_items_from_html(response_text)
        if items:
            return items
        
        # 3. 如果是API URL，尝试直接解析JSON
        if "/api/" in url:
            try:
                data = json.loads(response_text)
                items = self._extract_items_from_api_response(data)
                if items:
                    return items
            except json.JSONDecodeError:
                pass
        
        return trending_items
    
    def _extract_json_from_html(self, html: str) -> Optional[Dict]:
        """从HTML中提取JSON数据。
        
        Args:
            html: HTML文本
            
        Returns:
            提取的JSON数据，如果提取失败则返回None
        """
        # 尝试多种可能的JSON数据提取模式
        json_patterns = [
            r'<script>window\._SSR_HYDRATED_DATA=(.*?)</script>',
            r'<script id="RENDER_DATA" type="application/json">(.*?)</script>',
            r'window\._SSR_HYDRATED_DATA\s*=\s*({.*?});\s*</script>',
            r'__NEXT_DATA__\s*=\s*({.*?});\s*</script>',
            r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>',
            r'<script>var DATA = (.*?);</script>'
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, html, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).replace('undefined', 'null')
                try:
                    # 某些情况下可能需要URL解码
                    if pattern.find('RENDER_DATA') > -1 or pattern.find('__NEXT_DATA__') > -1:
                        import urllib.parse
                        json_str = urllib.parse.unquote(json_str)
                    data = json.loads(json_str)
                    logger.info(f"Successfully extracted JSON data using pattern: {pattern[:20]}...")
                    return data
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error with pattern {pattern[:20]}...: {e}")
                    continue
        
        return None
    
    def _extract_items_from_json(self, data: Dict) -> List[TrendingItem]:
        """从JSON数据中提取趋势项。
        
        Args:
            data: JSON数据
            
        Returns:
            提取的趋势项列表
        """
        trending_items = []
        
        # 尝试从JSON中提取热搜数据
        hot_board_data = self._extract_hot_board_data(data)
        
        if hot_board_data:
            for rank, item in enumerate(hot_board_data[:20], 1):
                if not isinstance(item, dict):
                    continue
                    
                # 尝试多种可能的字段名
                title = item.get("Title", "") or item.get("title", "") or item.get("content", "") or item.get("text", "")
                url = item.get("url", "") or item.get("link", "") or item.get("share_url", "") or item.get("target_url", "")
                
                if not title:
                    continue
                
                if not url:
                    url = f"https://www.toutiao.com/search/?keyword={title}"
                elif not url.startswith("http"):
                    url = f"https://www.toutiao.com{url}"
                    
                hot_value = item.get("HotValue", 0) or item.get("hot_value", 0) or item.get("score", 0) or item.get("raw_hot_value", 0) or item.get("heat", 0)
                description = item.get("Abstract", "") or item.get("abstract", "") or item.get("description", "") or item.get("desc", "") or item.get("summary", "")
                
                # 创建额外数据字典
                extra_data = {
                    "label": "",
                    "image_url": "",
                    "hot_value_display": "",
                    "tag": ""
                }
                
                # 安全地获取额外数据
                extra_data["label"] = item.get("Label", "") or item.get("label", "") or item.get("tag", "")
                
                # 安全地获取图片URL
                image = item.get("Image") or item.get("image") or item.get("thumbnail") or item.get("cover")
                if isinstance(image, dict):
                    extra_data["image_url"] = image.get("url", "") or image.get("src", "")
                else:
                    extra_data["image_url"] = item.get("image_url", "") or item.get("img", "")
                
                extra_data["hot_value_display"] = item.get("HotValueFormat", "") or item.get("hot_value_format", "") or item.get("display_hot_value", "")
                extra_data["tag"] = item.get("LabelDesc", "") or item.get("label_desc", "") or item.get("category", "")
                
                # 创建趋势项
                trending_items.append(
                    TrendingItem(
                        title=title,
                        url=url,
                        rank=rank,
                        score=float(hot_value) if hot_value and isinstance(hot_value, (int, float, str)) and str(hot_value).replace('.', '', 1).isdigit() else None,
                        author=None,
                        description=description,
                        timestamp=datetime.now(),
                        platform=self.name,
                        category="hot_search",
                        extra_data=extra_data
                    )
                )
        
        return trending_items
    
    def _extract_items_from_html(self, html: str) -> List[TrendingItem]:
        """从HTML中直接提取趋势项。
        
        Args:
            html: HTML文本
            
        Returns:
            提取的趋势项列表
        """
        trending_items = []
        
        # 使用正则表达式直接从HTML中提取热搜项
        # 尝试找到热搜列表
        hot_items_patterns = [
            r'<div[^>]*class="hot-board-list[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
            r'<div[^>]*class="hot-list[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
            r'<div[^>]*class="trending-board[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>'
        ]
        
        for pattern in hot_items_patterns:
            hot_items_match = re.search(pattern, html, re.DOTALL)
            if hot_items_match:
                hot_list_html = hot_items_match.group(1)
                
                # 提取每个热搜项
                item_patterns = [
                    r'<a[^>]*href="([^"]*)"[^>]*>.*?<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>.*?<div[^>]*class="[^"]*desc[^"]*"[^>]*>(.*?)</div>',
                    r'<a[^>]*href="([^"]*)"[^>]*>.*?<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>',
                    r'<a[^>]*href="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</span>'
                ]
                
                for item_pattern in item_patterns:
                    items = re.findall(item_pattern, hot_list_html, re.DOTALL)
                    if items:
                        for rank, item_tuple in enumerate(items[:20], 1):
                            # 根据匹配的模式处理数据
                            if len(item_tuple) == 3:  # URL, 标题, 描述
                                url, title, desc = item_tuple
                            elif len(item_tuple) == 2:  # URL, 标题
                                url, title = item_tuple
                                desc = ""
                            else:
                                continue
                            
                            # 清理HTML标签
                            title = re.sub(r'<[^>]*>', '', title).strip()
                            desc = re.sub(r'<[^>]*>', '', desc).strip() if desc else ""
                            
                            # 处理URL
                            if not url.startswith('http'):
                                url = f"https://www.toutiao.com{url}"
                            
                            trending_items.append(
                                TrendingItem(
                                    title=title,
                                    url=url,
                                    rank=rank,
                                    score=None,
                                    author=None,
                                    description=desc,
                                    timestamp=datetime.now(),
                                    platform=self.name,
                                    category="hot_search",
                                    extra_data={}
                                )
                            )
                        
                        if trending_items:
                            break
                
                if trending_items:
                    break
        
        # 如果正则表达式方法失败，使用BeautifulSoup尝试解析
        if not trending_items:
            logger.info("Using BeautifulSoup to parse HTML")
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试多种可能的CSS选择器
            selectors = [
                '.hot-board-item',
                '.hot-list-item',
                '.feed-card-item',
                '.channel-module-hot-list-item',
                '.hot-board__item',
                '[data-log-click]',
                'li[data-id]',
                '.trending-item',
                '.hot-item'
            ]
            
            hot_items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    hot_items = items
                    logger.info(f"Found hot items using selector: {selector}, count: {len(items)}")
                    break
            
            if hot_items:
                for rank, item in enumerate(hot_items[:20], 1):
                    # 尝试多种可能的标题选择器
                    title_selectors = [
                        '.title', '.hot-item-title', '.hot-board-item-title', 
                        'h3', 'h2', '.text-overflow', '[title]'
                    ]
                    
                    title_elem = None
                    for selector in title_selectors:
                        elem = item.select_one(selector)
                        if elem:
                            title_elem = elem
                            break
                    
                    if not title_elem:
                        # 如果没有找到标题元素，尝试获取item的文本内容
                        title = item.get_text(strip=True)
                        # 如果文本太长，可能不是标题
                        if len(title) > 50:
                            continue
                    else:
                        title = title_elem.get_text(strip=True)
                    
                    # 尝试获取URL
                    url_elem = item.select_one('a') or title_elem.parent if title_elem else None
                    url = ""
                    if url_elem and url_elem.has_attr('href'):
                        url = url_elem['href']
                        if not url.startswith('http'):
                            url = f"https://www.toutiao.com{url}"
                    else:
                        url = f"https://www.toutiao.com/search/?keyword={title}"
                    
                    # 尝试获取描述
                    desc_selectors = [
                        '.abstract', '.hot-item-desc', '.hot-board-item-desc',
                        '.desc', '.description', '.content', 'p'
                    ]
                    
                    desc_elem = None
                    for selector in desc_selectors:
                        elem = item.select_one(selector)
                        if elem:
                            desc_elem = elem
                            break
                    
                    description = desc_elem.get_text(strip=True) if desc_elem else None
                    
                    trending_items.append(
                        TrendingItem(
                            title=title,
                            url=url,
                            rank=rank,
                            score=None,
                            author=None,
                            description=description,
                            timestamp=datetime.now(),
                            platform=self.name,
                            category="hot_search",
                            extra_data={}
                        )
                    )
        
        return trending_items
    
    def _extract_items_from_api_response(self, data: Dict) -> List[TrendingItem]:
        """从API响应中提取趋势项。
        
        Args:
            data: API响应数据
            
        Returns:
            提取的趋势项列表
        """
        trending_items = []
        
        # 尝试多种可能的数据路径
        data_paths = [
            ["data", "data"],
            ["data"],
            ["result", "data"],
            ["result"]
        ]
        
        items_list = None
        for path in data_paths:
            current = data
            valid_path = True
            
            for key in path:
                if not isinstance(current, dict) or key not in current:
                    valid_path = False
                    break
                current = current[key]
            
            if valid_path and isinstance(current, list) and current:
                items_list = current
                break
        
        if not items_list:
            return trending_items
        
        # 处理找到的项目列表
        for rank, item in enumerate(items_list[:20], 1):
            if not isinstance(item, dict):
                continue
                
            # 尝试多种可能的字段名
            title = item.get("title", "") or item.get("content", "") or item.get("text", "")
            url = item.get("url", "") or item.get("link", "") or item.get("share_url", "")
            
            if not title:
                continue
            
            if not url:
                url = f"https://www.toutiao.com/search/?keyword={title}"
            elif not url.startswith("http"):
                url = f"https://www.toutiao.com{url}"
                
            description = item.get("abstract", "") or item.get("description", "") or item.get("desc", "")
            
            trending_items.append(
                TrendingItem(
                    title=title,
                    url=url,
                    rank=rank,
                    score=None,
                    author=None,
                    description=description,
                    timestamp=datetime.now(),
                    platform=self.name,
                    category="hot_search",
                    extra_data={}
                )
            )
        
        return trending_items
    
    def _extract_hot_board_data(self, data):
        """从JSON数据中提取热搜数据。
        
        Args:
            data: JSON数据
            
        Returns:
            热搜数据列表，如果未找到则返回空列表
        """
        if not data or not isinstance(data, dict):
            return []
            
        # 尝试多种可能的数据路径
        possible_paths = [
            ["ChineseHotBoard", "hotBoard", "data"],
            ["data", "ChineseHotBoard", "hotBoard", "data"],
            ["props", "pageProps", "hotBoard", "data"],
            ["props", "pageProps", "data", "hotBoard"],
            ["props", "initialState", "hotBoard", "data"],
            ["initialState", "hotBoard", "data"]
        ]
        
        for path in possible_paths:
            current = data
            valid_path = True
            
            for key in path:
                if not isinstance(current, dict) or key not in current:
                    valid_path = False
                    break
                current = current[key]
            
            if valid_path and isinstance(current, list) and current:
                logger.info(f"Found hot board data using path: {path}")
                return current
        
        # 递归查找可能包含热搜数据的列表
        def find_hot_board_data(obj, depth=0, max_depth=3):
            if depth >= max_depth:
                return None
            
            if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
                # 检查是否是热搜数据列表
                keys_to_check = ["title", "url", "hot_value", "image"]
                first_item = obj[0]
                
                # 检查是否至少有2个关键字段
                matches = sum(1 for key in keys_to_check if key in first_item or key.capitalize() in first_item)
                if matches >= 2:
                    return obj
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # 优先检查可能包含热搜数据的键
                    if key.lower().find("hot") >= 0 or key.lower().find("board") >= 0 or key.lower().find("list") >= 0:
                        result = find_hot_board_data(value, depth + 1, max_depth)
                        if result:
                            return result
                    
                # 检查所有其他键
                for key, value in obj.items():
                    if key.lower().find("hot") < 0 and key.lower().find("board") < 0 and key.lower().find("list") < 0:
                        result = find_hot_board_data(value, depth + 1, max_depth)
                        if result:
                            return result
            
            return None
        
        hot_board_data = find_hot_board_data(data)
        if hot_board_data:
            logger.info(f"Found hot board data using recursive search, items: {len(hot_board_data)}")
            return hot_board_data
            
        return []
