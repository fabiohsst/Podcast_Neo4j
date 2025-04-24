# Importing libraries
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Set
import csv

# Base URL of the website to scrape.
BASE_URL: str = 'https://www.b9.com.br'

# Custom headers to mimic a real browser request.
HEADERS: dict[str, str] = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/90.0.4430.93 Safari/537.36'
    )
}


def get_soup(url: str) -> BeautifulSoup:
    """
    Fetch the content from the given URL and return a BeautifulSoup object
    for parsing the HTML.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        BeautifulSoup: A BeautifulSoup object containing the parsed HTML.

    Raises:
        HTTPError: If the HTTP request fails (non-200 status code).
    """
    # Send a GET request with custom headers.
    response = requests.get(url, headers=HEADERS)
    # Raise an error for bad responses (e.g., 404, 500).
    response.raise_for_status()
    # Set the encoding to UTF-8 to properly interpret the response.
    response.encoding = 'utf-8'
    # Parse and return the HTML content using the built-in parser.
    return BeautifulSoup(response.text, 'html.parser')


def extract_references(post_url: str) -> List[str]:
    """
    Extract a list of reference strings from a post page.

    This function looks for a paragraph element containing the text
    'REFERÊNCIAS'. It then collects the text from all subsequent sibling
    elements until it encounters a sibling with the text '========', which is
    used as a delimiter to mark the end of the references section.

    Args:
        post_url (str): The URL of the post containing references.

    Returns:
        List[str]: A list of reference strings. If no references section is found,
                   an empty list is returned.
    """
    # Retrieve and parse the HTML of the post page.
    soup = get_soup(post_url)
    
    # Locate the paragraph element that contains 'REFERÊNCIAS'.
    references_section = soup.find('p', string=lambda x: x and 'REFERÊNCIAS' in x)
    if not references_section:
        return []
    
    references: List[str] = []
    # Iterate over all sibling elements that follow the references section.
    for sibling in references_section.find_next_siblings():
        text = sibling.get_text(strip=True)
        # Stop collecting references when encountering the delimiter.
        if text == '========':
            break
        references.append(text)
    
    return references

# Example usage:
if __name__ == '__main__':
    # Replace 'your_post_url' with the actual URL you want to scrape.
    your_post_url = 'https://www.b9.com.br/shows/naruhodo/naruhodo-418-o-que-e-a-birra/?highlight=naruhodo'
    refs = extract_references(your_post_url)
    for ref in refs:
        print(ref)
