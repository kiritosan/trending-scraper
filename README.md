# Trending Content Scraper

A modern Python framework for scraping trending content from various platforms like Bilibili and Toutiao.

## Features

- Command-line interface for easy usage
- Modular architecture for adding new platforms
- Async support for efficient data fetching
- Rich terminal output formatting
- Type hints throughout the codebase

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trending-scraper.git
cd trending-scraper

# Install the package in development mode
pip install -e .
```

## Usage

```bash
# Get trending content from Bilibili
trending bilibili

# Get trending content from Toutiao
trending toutiao

# Get trending content from all supported platforms
trending all

# Get help
trending --help
```

## Adding a New Platform

To add support for a new platform, create a new file in the `trending_scraper/scrapers` directory and implement the `BaseScraper` interface.

## License

MIT
