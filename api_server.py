"""API server for trending-scraper."""

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem, logger
from trending_scraper.cache import get_cache, set_cache, get_all_cache
from trending_scraper.scheduler import start_scheduler

app = FastAPI(title="Trending Scraper API", description="API for trending content from various platforms")

# 添加CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储调度器任务的引用
scheduler_task = None

@app.on_event("startup")
async def startup_event():
    """应用启动时执行的事件。"""
    global scheduler_task
    # 启动调度器
    scheduler_task = start_scheduler()
    # 立即执行一次缓存更新
    from trending_scraper.scheduler import update_all_cache
    await update_all_cache()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的事件。"""
    global scheduler_task
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled")

@app.get("/")
async def root():
    """API根路径，返回可用端点信息。"""
    return {
        "message": "Welcome to Trending Scraper API",
        "endpoints": {
            "platforms": "/platforms",
            "trending": "/trending/{platform}",
            "trending_all": "/trending"
        }
    }

@app.get("/platforms")
async def get_platforms():
    """获取所有支持的平台。"""
    scrapers = BaseScraper.get_all_scrapers()
    return {
        "platforms": [
            {
                "id": name,
                "name": scraper.display_name
            }
            for name, scraper in scrapers.items()
        ]
    }

@app.get("/trending/{platform}")
async def get_trending(platform: str, limit: int = 10, force_refresh: bool = False):
    """获取指定平台的热门内容。
    
    Args:
        platform: 平台ID
        limit: 返回的热门项数量
        force_refresh: 是否强制刷新缓存
    """
    scrapers = BaseScraper.get_all_scrapers()
    
    if platform not in scrapers:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not found")
    
    # 如果不强制刷新，尝试从缓存获取
    if not force_refresh:
        cached_data = get_cache(platform)
        if cached_data:
            # 限制返回的项目数量
            cached_data["items"] = cached_data["items"][:limit]
            return cached_data
    
    # 缓存不存在、已过期或强制刷新，获取新数据
    try:
        logger.info(f"Fetching fresh data for {platform}")
        items = await scrapers[platform].get_trending()
        items = sorted(items, key=lambda x: x.rank)[:limit]
        
        result = {
            "platform": platform,
            "display_name": scrapers[platform].display_name,
            "items": [item.dict() for item in items]
        }
        
        # 更新缓存
        set_cache(platform, result)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching trending content from {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching data from {platform}")

@app.get("/trending")
async def get_all_trending(limit: int = 10, force_refresh: bool = False):
    """获取所有平台的热门内容。
    
    Args:
        limit: 每个平台返回的热门项数量
        force_refresh: 是否强制刷新缓存
    """
    scrapers = BaseScraper.get_all_scrapers()
    
    if not scrapers:
        return {"platforms": []}
    
    # 如果不强制刷新，尝试从缓存获取所有平台数据
    if not force_refresh:
        all_cache = get_all_cache()
        if all_cache:
            platforms_data = list(all_cache.values())
            # 限制每个平台返回的项目数量
            for platform_data in platforms_data:
                platform_data["items"] = platform_data["items"][:limit]
            return {"platforms": platforms_data}
    
    # 缓存不存在、已过期或强制刷新，获取新数据
    results = []
    for name, scraper in scrapers.items():
        try:
            logger.info(f"Fetching fresh data for {name}")
            items = await scraper.get_trending()
            items = sorted(items, key=lambda x: x.rank)[:limit]
            
            platform_data = {
                "platform": name,
                "display_name": scraper.display_name,
                "items": [item.dict() for item in items]
            }
            
            # 更新缓存
            set_cache(name, platform_data)
            
            results.append(platform_data)
        except Exception as e:
            # 如果某个平台出错，继续获取其他平台的数据
            logger.error(f"Error fetching trending content from {scraper.display_name}: {e}")
    
    return {"platforms": results}

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
