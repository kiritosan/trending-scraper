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


async def fetch_async(url: str, headers: Optional[Dict[str, str]] = None) -> str:
    """Fetch content from URL asynchronously.
    
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
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.text()


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
