"""调度器模块，用于定期更新缓存数据。"""

import asyncio
from datetime import datetime

from trending_scraper.scrapers import BaseScraper
from trending_scraper.cache import set_cache
from trending_scraper.utils import logger

async def update_all_cache() -> None:
    """更新所有平台的缓存数据。"""
    scrapers = BaseScraper.get_all_scrapers()
    
    for name, scraper in scrapers.items():
        try:
            logger.info(f"Scheduled update for {scraper.display_name}")
            items = await scraper.get_trending()
            items = sorted(items, key=lambda x: x.rank)
            
            # 准备缓存数据
            cache_data = {
                "platform": name,
                "display_name": scraper.display_name,
                "items": [item.dict() for item in items]
            }
            
            # 更新缓存
            set_cache(name, cache_data)
            logger.info(f"Updated cache for {scraper.display_name}, items: {len(items)}")
        except Exception as e:
            logger.error(f"Error updating cache for {scraper.display_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())

async def scheduler_task() -> None:
    """调度器任务，每5分钟运行一次更新。"""
    while True:
        try:
            logger.info("Running scheduled cache update")
            await update_all_cache()
            logger.info("Scheduled cache update completed")
        except Exception as e:
            logger.error(f"Error in scheduler task: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        # 等待5分钟
        logger.info("Scheduler waiting for next update cycle")
        await asyncio.sleep(5 * 60)  # 5分钟

def start_scheduler() -> asyncio.Task:
    """启动调度器任务。
    
    Returns:
        调度器任务对象
    """
    logger.info("Starting scheduler")
    return asyncio.create_task(scheduler_task())
