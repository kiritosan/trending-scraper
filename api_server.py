"""API server for trending-scraper."""

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem

app = FastAPI(title="Trending Scraper API", description="API for trending content from various platforms")

# 添加CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def get_trending(platform: str, limit: int = 10):
    """获取指定平台的热门内容。"""
    scrapers = BaseScraper.get_all_scrapers()
    
    if platform not in scrapers:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not found")
    
    items = await scrapers[platform].get_trending()
    items = sorted(items, key=lambda x: x.rank)[:limit]
    
    return {
        "platform": platform,
        "display_name": scrapers[platform].display_name,
        "items": [item.dict() for item in items]
    }

@app.get("/trending")
async def get_all_trending(limit: int = 10):
    """获取所有平台的热门内容。"""
    scrapers = BaseScraper.get_all_scrapers()
    
    if not scrapers:
        return {"platforms": []}
    
    results = []
    for name, scraper in scrapers.items():
        try:
            items = await scraper.get_trending()
            items = sorted(items, key=lambda x: x.rank)[:limit]
            
            results.append({
                "platform": name,
                "display_name": scraper.display_name,
                "items": [item.dict() for item in items]
            })
        except Exception as e:
            # 如果某个平台出错，继续获取其他平台的数据
            print(f"Error fetching trending content from {scraper.display_name}: {e}")
    
    return {"platforms": results}

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
