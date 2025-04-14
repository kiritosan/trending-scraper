"""Command-line interface for the trending content scraper."""

import asyncio
import sys
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

from trending_scraper.scrapers import BaseScraper
from trending_scraper.utils import TrendingItem, logger


console = Console()


def display_trending_items(items: List[TrendingItem], platform: str) -> None:
    """Display trending items in a rich table.
    
    Args:
        items: List of trending items to display
        platform: Platform name
    """
    if not items:
        console.print(f"[yellow]No trending items found for {platform}[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Trending on {platform}")
    
    # Add columns
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Title", style="green")
    table.add_column("Score", style="magenta", justify="right")
    table.add_column("Category", style="blue")
    
    # Add rows
    for item in items:
        table.add_row(
            str(item.rank),
            item.title,
            str(item.score) if item.score is not None else "N/A",
            item.category or "N/A"
        )
    
    # Print table
    console.print(table)
    console.print()


@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Trending content scraper for various platforms."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option(
    "--limit", "-l", 
    type=int, 
    default=10, 
    help="Limit the number of trending items to display"
)
def bilibili(limit: int) -> None:
    """Get trending content from Bilibili."""
    scrapers = BaseScraper.get_all_scrapers()
    if "bilibili" not in scrapers:
        console.print("[red]Bilibili scraper not found[/red]")
        return
    
    with console.status("[bold green]Fetching trending content from Bilibili..."):
        items = asyncio.run(scrapers["bilibili"].get_trending())
        items = sorted(items, key=lambda x: x.rank)[:limit]
    
    display_trending_items(items, "Bilibili")


@main.command()
@click.option(
    "--limit", "-l", 
    type=int, 
    default=10, 
    help="Limit the number of trending items to display"
)
def toutiao(limit: int) -> None:
    """Get trending content from Toutiao."""
    scrapers = BaseScraper.get_all_scrapers()
    if "toutiao" not in scrapers:
        console.print("[red]Toutiao scraper not found[/red]")
        return
    
    with console.status("[bold green]Fetching trending content from Toutiao..."):
        items = asyncio.run(scrapers["toutiao"].get_trending())
        items = sorted(items, key=lambda x: x.rank)[:limit]
    
    display_trending_items(items, "今日头条")


@main.command()
@click.option(
    "--limit", "-l", 
    type=int, 
    default=10, 
    help="Limit the number of trending items to display per platform"
)
def all(limit: int) -> None:
    """Get trending content from all supported platforms."""
    scrapers = BaseScraper.get_all_scrapers()
    
    if not scrapers:
        console.print("[red]No scrapers found[/red]")
        return
    
    for name, scraper in scrapers.items():
        with console.status(f"[bold green]Fetching trending content from {scraper.display_name}..."):
            items = asyncio.run(scraper.get_trending())
            items = sorted(items, key=lambda x: x.rank)[:limit]
        
        display_trending_items(items, scraper.display_name)


if __name__ == "__main__":
    main()
