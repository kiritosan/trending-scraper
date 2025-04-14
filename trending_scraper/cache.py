"""缓存模块，用于存储和管理爬虫数据。"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from trending_scraper.utils import logger

# 全局缓存
trending_cache: Dict[str, Dict[str, Any]] = {}
CACHE_EXPIRY = timedelta(minutes=5)

def get_cache(platform: str) -> Optional[Dict[str, Any]]:
    """获取指定平台的缓存数据。
    
    Args:
        platform: 平台ID
        
    Returns:
        缓存数据，如果缓存不存在或已过期则返回None
    """
    if platform not in trending_cache:
        return None
        
    cache_entry = trending_cache[platform]
    current_time = datetime.now()
    
    # 检查缓存是否过期
    if current_time - cache_entry["timestamp"] > CACHE_EXPIRY:
        logger.info(f"Cache for {platform} expired")
        return None
        
    logger.info(f"Using cache for {platform}, age: {current_time - cache_entry['timestamp']}")
    return cache_entry["data"]
    
def set_cache(platform: str, data: Dict[str, Any]) -> None:
    """设置指定平台的缓存数据。
    
    Args:
        platform: 平台ID
        data: 要缓存的数据
    """
    trending_cache[platform] = {
        "data": data,
        "timestamp": datetime.now()
    }
    logger.info(f"Updated cache for {platform}")
    
def get_all_cache() -> Dict[str, Dict[str, Any]]:
    """获取所有未过期的缓存数据。
    
    Returns:
        所有未过期的缓存数据
    """
    result = {}
    current_time = datetime.now()
    
    for platform, cache_entry in trending_cache.items():
        if current_time - cache_entry["timestamp"] <= CACHE_EXPIRY:
            result[platform] = cache_entry["data"]
            
    return result
