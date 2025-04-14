"""Utility functions for the trending content scraper."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp
import requests
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TrendingItem(BaseModel):
    """Model representing a trending item."""

    title: str
    url: str
    rank: int
    score: Optional[float] = None
    author: Optional[str] = None
    description: Optional[str] = None
    timestamp: Optional[datetime] = None
    platform: str
    category: Optional[str] = None
    extra_data: Dict[str, Any] = {}


async def fetch_async(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> str:
    """Fetch URL asynchronously.
    
    Args:
        url: URL to fetch
        headers: Optional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response text
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache"
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=default_headers, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        raise


def fetch_sync(url: str, headers: Optional[Dict[str, str]] = None) -> str:
    """Fetch content from URL synchronously.
    
    Args:
        url: The URL to fetch content from
        headers: Optional HTTP headers
        
    Returns:
        The response text
    """
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text
