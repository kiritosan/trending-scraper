"""Tests for the command-line interface."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner

from trending_scraper.cli import main, display_trending_items
from trending_scraper.utils import TrendingItem


class TestCLI:
    """Tests for the CLI functions."""

    @pytest.fixture
    def runner(self):
        """Fixture for CliRunner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_trending_items(self):
        """Fixture for mock trending items."""
        return [
            TrendingItem(
                title="Test Item 1",
                url="https://example.com/1",
                rank=1,
                score=100,
                author="Test Author 1",
                platform="test_platform",
                category="test_category"
            ),
            TrendingItem(
                title="Test Item 2",
                url="https://example.com/2",
                rank=2,
                score=None,
                author=None,
                platform="test_platform",
                category=None
            )
        ]
    
    def test_display_trending_items(self, mock_trending_items):
        """Test display_trending_items function."""
        with patch("trending_scraper.cli.console") as mock_console:
            # Call the function with mock items
            display_trending_items(mock_trending_items, "Test Platform")
            
            # Check that console.print was called
            assert mock_console.print.call_count >= 2
    
    def test_display_trending_items_empty(self):
        """Test display_trending_items function with empty list."""
        with patch("trending_scraper.cli.console") as mock_console:
            # Call the function with empty list
            display_trending_items([], "Test Platform")
            
            # Check that console.print was called with the expected message
            mock_console.print.assert_called_once()
            args = mock_console.print.call_args[0][0]
            assert "No trending items found" in args
            assert "Test Platform" in args
    
    def test_main_help(self, runner):
        """Test main command with --help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Trending content scraper for various platforms" in result.output
    
    def test_main_no_args(self, runner):
        """Test main command with no arguments."""
        result = runner.invoke(main)
        assert result.exit_code == 0
        assert "Trending content scraper for various platforms" in result.output
    
    def test_bilibili_command(self, runner, mock_trending_items):
        """Test bilibili command."""
        # Mock the BaseScraper.get_all_scrapers method
        mock_scraper = MagicMock()
        mock_scraper.get_trending = AsyncMock(return_value=mock_trending_items)
        
        with patch("trending_scraper.cli.BaseScraper.get_all_scrapers", return_value={"bilibili": mock_scraper}), \
             patch("trending_scraper.cli.asyncio.run"), \
             patch("trending_scraper.cli.display_trending_items") as mock_display:
            
            # Call the command
            result = runner.invoke(main, ["bilibili"])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that the scraper's get_trending method was called
            mock_scraper.get_trending.assert_called_once()
            
            # Check that display_trending_items was called
            mock_display.assert_called_once()
    
    def test_bilibili_command_not_found(self, runner):
        """Test bilibili command when scraper is not found."""
        with patch("trending_scraper.cli.BaseScraper.get_all_scrapers", return_value={}), \
             patch("trending_scraper.cli.console") as mock_console:
            
            # Call the command
            result = runner.invoke(main, ["bilibili"])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that console.print was called with the expected message
            mock_console.print.assert_called_once()
            args = mock_console.print.call_args[0][0]
            assert "Bilibili scraper not found" in args
    
    def test_toutiao_command(self, runner, mock_trending_items):
        """Test toutiao command."""
        # Mock the BaseScraper.get_all_scrapers method
        mock_scraper = MagicMock()
        mock_scraper.get_trending = AsyncMock(return_value=mock_trending_items)
        
        with patch("trending_scraper.cli.BaseScraper.get_all_scrapers", return_value={"toutiao": mock_scraper}), \
             patch("trending_scraper.cli.asyncio.run"), \
             patch("trending_scraper.cli.display_trending_items") as mock_display:
            
            # Call the command
            result = runner.invoke(main, ["toutiao"])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that the scraper's get_trending method was called
            mock_scraper.get_trending.assert_called_once()
            
            # Check that display_trending_items was called
            mock_display.assert_called_once()
    
    def test_all_command(self, runner, mock_trending_items):
        """Test all command."""
        # Mock the BaseScraper.get_all_scrapers method
        mock_bilibili_scraper = MagicMock()
        mock_bilibili_scraper.get_trending = AsyncMock(return_value=mock_trending_items)
        mock_bilibili_scraper.display_name = "Bilibili"
        
        mock_toutiao_scraper = MagicMock()
        mock_toutiao_scraper.get_trending = AsyncMock(return_value=mock_trending_items)
        mock_toutiao_scraper.display_name = "今日头条"
        
        scrapers = {
            "bilibili": mock_bilibili_scraper,
            "toutiao": mock_toutiao_scraper
        }
        
        with patch("trending_scraper.cli.BaseScraper.get_all_scrapers", return_value=scrapers), \
             patch("trending_scraper.cli.asyncio.run"), \
             patch("trending_scraper.cli.display_trending_items") as mock_display:
            
            # Call the command
            result = runner.invoke(main, ["all"])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that each scraper's get_trending method was called
            mock_bilibili_scraper.get_trending.assert_called_once()
            mock_toutiao_scraper.get_trending.assert_called_once()
            
            # Check that display_trending_items was called twice (once for each scraper)
            assert mock_display.call_count == 2
    
    def test_all_command_no_scrapers(self, runner):
        """Test all command when no scrapers are found."""
        with patch("trending_scraper.cli.BaseScraper.get_all_scrapers", return_value={}), \
             patch("trending_scraper.cli.console") as mock_console:
            
            # Call the command
            result = runner.invoke(main, ["all"])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that console.print was called with the expected message
            mock_console.print.assert_called_once()
            args = mock_console.print.call_args[0][0]
            assert "No scrapers found" in args
