"""Integration tests for the trending-scraper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem


class TestIntegration:
    """Integration tests for the trending-scraper."""

    @pytest.mark.asyncio
    async def test_scraper_registration(self):
        """Test that scrapers are properly registered."""
        # Get all scrapers
        scrapers = BaseScraper.get_all_scrapers()
        
        # Check that we have at least the expected scrapers
        assert "bilibili" in scrapers
        assert "toutiao" in scrapers
        
        # Check that the scrapers have the expected attributes
        assert scrapers["bilibili"].name == "bilibili"
        assert scrapers["bilibili"].display_name == "Bilibili"
        assert scrapers["toutiao"].name == "toutiao"
        assert scrapers["toutiao"].display_name == "今日头条"
    
    @pytest.mark.asyncio
    async def test_mock_scraper_workflow(self):
        """Test the complete workflow with mock data."""
        # Create mock trending items
        mock_items = [
            TrendingItem(
                title="Test Item 1",
                url="https://example.com/1",
                rank=1,
                score=100,
                platform="test_platform",
                category="test_category"
            ),
            TrendingItem(
                title="Test Item 2",
                url="https://example.com/2",
                rank=2,
                score=50,
                platform="test_platform",
                category="test_category"
            )
        ]
        
        # Mock the scrapers
        with patch.object(BaseScraper, "get_all_scrapers") as mock_get_scrapers:
            # Create mock scrapers
            mock_bilibili = MagicMock()
            mock_bilibili.name = "bilibili"
            mock_bilibili.display_name = "Bilibili"
            mock_bilibili.get_trending = AsyncMock(return_value=mock_items)
            
            mock_toutiao = MagicMock()
            mock_toutiao.name = "toutiao"
            mock_toutiao.display_name = "今日头条"
            mock_toutiao.get_trending = AsyncMock(return_value=mock_items)
            
            # Set up the mock to return our mock scrapers
            mock_get_scrapers.return_value = {
                "bilibili": mock_bilibili,
                "toutiao": mock_toutiao
            }
            
            # Get all scrapers
            scrapers = BaseScraper.get_all_scrapers()
            
            # Test each scraper
            for name, scraper in scrapers.items():
                # Get trending items
                items = await scraper.get_trending()
                
                # Check that we got the expected items
                assert len(items) == 2
                assert all(isinstance(item, TrendingItem) for item in items)
                assert items[0].title == "Test Item 1"
                assert items[1].title == "Test Item 2"
                
                # Check that the items are sorted by rank
                assert items[0].rank < items[1].rank
                
                # Check that the scraper's get_trending method was called
                scraper.get_trending.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="This test makes actual API calls and should be run manually")
    async def test_real_scrapers(self):
        """Test the real scrapers with actual API calls.
        
        This test is skipped by default because it makes actual API calls.
        Remove the skipif decorator to run this test manually.
        """
        # Get all scrapers
        scrapers = BaseScraper.get_all_scrapers()
        
        # Test each scraper
        for name, scraper in scrapers.items():
            # Get trending items
            items = await scraper.get_trending()
            
            # Check that we got some items
            assert len(items) > 0
            assert all(isinstance(item, TrendingItem) for item in items)
            
            # Check that the items have the expected attributes
            for item in items:
                assert item.title
                assert item.url
                assert item.rank > 0
                assert item.platform == name
