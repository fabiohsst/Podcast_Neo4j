"""
collect_references.py
Collect podcast post URLs, scrape references, and save to CSV for Naruhodo Podcast project.
"""

from typing import List


def get_podcast_posts(page_number: int) -> List[str]:
    """
    Collect all podcast post URLs from a given page number.
    """
    # TODO: Implement URL collection logic
    pass


def scrape_references() -> List[List[str]]:
    """
    Scrape references for all collected podcast posts.
    """
    # TODO: Implement scraping logic for all posts
    pass


def save_to_csv(data: List[List[str]], filename: str = 'references3.csv') -> None:
    """
    Save the scraped references data to a CSV file.
    """
    # TODO: Implement CSV saving logic
    pass 