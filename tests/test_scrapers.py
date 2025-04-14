"""Tests for scrapers."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from trending_scraper.scrapers import BaseScraper
from trending_scraper.scrapers.bilibili import BilibiliScraper
from trending_scraper.scrapers.toutiao import ToutiaoScraper
from trending_scraper.utils import TrendingItem


class TestBaseScraper:
    """Tests for the BaseScraper class."""

    def test_get_scraper_classes(self):
        """Test get_scraper_classes method."""
        scraper_classes = BaseScraper.get_scraper_classes()
        
        # Check that the method returns a dictionary
        assert isinstance(scraper_classes, dict)
        
        # Check that the dictionary contains the expected scrapers
        assert "bilibili" in scraper_classes
        assert "toutiao" in scraper_classes
        
        # Check that the values are the expected classes
        assert scraper_classes["bilibili"] == BilibiliScraper
        assert scraper_classes["toutiao"] == ToutiaoScraper
    
    def test_get_all_scrapers(self):
        """Test get_all_scrapers method."""
        scrapers = BaseScraper.get_all_scrapers()
        
        # Check that the method returns a dictionary
        assert isinstance(scrapers, dict)
        
        # Check that the dictionary contains the expected scrapers
        assert "bilibili" in scrapers
        assert "toutiao" in scrapers
        
        # Check that the values are instances of the expected classes
        assert isinstance(scrapers["bilibili"], BilibiliScraper)
        assert isinstance(scrapers["toutiao"], ToutiaoScraper)


class TestBilibiliScraper:
    """Tests for the BilibiliScraper class."""

    @pytest.fixture
    def bilibili_scraper(self):
        """Fixture for BilibiliScraper instance."""
        return BilibiliScraper()
    
    @pytest.fixture
    def mock_video_response(self):
        """Fixture for mock video API response."""
        return {
            "code": 0,
            "data": {
                "list": [
                    {
                        "title": "Test Video",
                        "bvid": "BV123456789",
                        "score": 100,
                        "owner": {"name": "Test User"},
                        "desc": "Test Description",
                        "pubdate": 1617235200,  # 2021-04-01 00:00:00
                        "stat": {
                            "view": 1000,
                            "danmaku": 100,
                            "like": 50
                        },
                        "duration": 300
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_topic_response(self):
        """Fixture for mock topic API response."""
        return {
            "code": 0,
            "data": {
                "trending": {
                    "list": [
                        {
                            "keyword": "Test Topic",
                            "hot_score": 200,
                            "show_name": "Test Topic Description",
                            "icon": "test_icon",
                            "type": "test_type"
                        }
                    ]
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_get_trending_videos(self, bilibili_scraper, mock_video_response):
        """Test _get_trending_videos method."""
        with patch("trending_scraper.scrapers.bilibili.fetch_async", AsyncMock(return_value=json.dumps(mock_video_response))):
            result = await bilibili_scraper._get_trending_videos()
            
            # Check that the method returns a list
            assert isinstance(result, list)
            assert len(result) == 1
            
            # Check that the list contains TrendingItem objects
            item = result[0]
            assert isinstance(item, TrendingItem)
            
            # Check that the TrendingItem has the expected values
            assert item.title == "Test Video"
            assert item.url == "https://www.bilibili.com/video/BV123456789"
            assert item.rank == 1
            assert item.score == 100
            assert item.author == "Test User"
            assert item.description == "Test Description"
            assert item.platform == "bilibili"
            assert item.category == "video"
            
            # Check extra_data
            assert item.extra_data["play_count"] == 1000
            assert item.extra_data["danmaku_count"] == 100
            assert item.extra_data["like_count"] == 50
            assert item.extra_data["duration"] == 300
    
    @pytest.mark.asyncio
    async def test_get_trending_topics(self, bilibili_scraper, mock_topic_response):
        """Test _get_trending_topics method."""
        with patch("trending_scraper.scrapers.bilibili.fetch_async", AsyncMock(return_value=json.dumps(mock_topic_response))):
            result = await bilibili_scraper._get_trending_topics()
            
            # Check that the method returns a list
            assert isinstance(result, list)
            assert len(result) == 1
            
            # Check that the list contains TrendingItem objects
            item = result[0]
            assert isinstance(item, TrendingItem)
            
            # Check that the TrendingItem has the expected values
            assert item.title == "Test Topic"
            assert item.url == "https://search.bilibili.com/all?keyword=Test Topic"
            assert item.rank == 1
            assert item.score == 200
            assert item.description == "Test Topic Description"
            assert item.platform == "bilibili"
            assert item.category == "topic"
            
            # Check extra_data
            assert item.extra_data["icon"] == "test_icon"
            assert item.extra_data["topic_type"] == "test_type"
    
    @pytest.mark.asyncio
    async def test_get_trending(self, bilibili_scraper):
        """Test get_trending method."""
        # Create mock items
        video_item = TrendingItem(
            title="Test Video",
            url="https://example.com/video",
            rank=1,
            platform="bilibili",
            category="video"
        )
        topic_item = TrendingItem(
            title="Test Topic",
            url="https://example.com/topic",
            rank=1,
            platform="bilibili",
            category="topic"
        )
        
        # Mock the internal methods
        bilibili_scraper._get_trending_videos = AsyncMock(return_value=[video_item])
        bilibili_scraper._get_trending_topics = AsyncMock(return_value=[topic_item])
        
        # Call the method
        result = await bilibili_scraper.get_trending()
        
        # Check that the method returns a list with both items
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == video_item
        assert result[1] == topic_item
        
        # Check that the internal methods were called
        bilibili_scraper._get_trending_videos.assert_called_once()
        bilibili_scraper._get_trending_topics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_trending_with_exception(self, bilibili_scraper):
        """Test get_trending method with exception."""
        # Mock the internal methods to raise an exception
        bilibili_scraper._get_trending_videos = AsyncMock(side_effect=Exception("Test error"))
        
        # Call the method
        result = await bilibili_scraper.get_trending()
        
        # Check that the method returns an empty list
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Check that the internal method was called
        bilibili_scraper._get_trending_videos.assert_called_once()
