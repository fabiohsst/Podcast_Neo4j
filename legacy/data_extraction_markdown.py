# %% [markdown]
# # Naruhodo Podcast Graph Database
# 
# **Naruhodo** is a Brazilian podcast dedicated to answering listeners’ questions about science, common sense, and curiosities. Every episode is packed with science-based content and is enriched with a diverse set of references—ranging from scientific papers and articles to books and online resources. Many episodes share overlapping themes and often reference the same sources, which makes the dataset ideal for creating an interconnected graph.
# 
# This project focuses on scraping the available Naruhodo podcast data and importing it into Neo4j. The primary objective here is to efficiently collect and structure the data into a graph database, establishing a robust foundation. Future projects will build upon this groundwork to reveal connections between episodes, identify clusters of related themes, and explore how references bridge multiple subjects.
# 
# ## Table of Contents
# 
# - [Introduction](#introduction)
# - [Project Structure](#project-structure)
# - [Environment and Dependencies](#Environment-and-dependencies)
# - [Code Breakdown](#Code-breakdown)
#   - [1. Data Scraping Module](#data-scraping-module)
#   - [2. Data Collection and CSV Generation](#data-collection-and-csv-generation)
#   - [3. CSV Normalization](#csv-normalization)
#   - [4. Neo4j Data Import](#neo4j-data-import)
# - [Analytical Possibilities in Neo4j](#analytical-possibilities-in-neo4j)
# - [Conclusion](#conclusion)
# 

# %% [markdown]
# <a name="introduction"></a>
# ## Introduction
# 
# *Naruhodo* is not only a podcast—it’s a curated collection of scientific exploration where episodes often intersect through shared references. **The primary goal of this notebook is to scrape the available Naruhodo podcast data and import it into Neo4j, creating a robust graph database foundation.** Further projects utilizing this dataset will be developed in separate notebooks.
# 
# This foundational project opens up a wide range of future possibilities, especially with the integration of LLMs and Machine Learning. Here are the top 5 potential projects that can be pursued once the data is in Neo4j:
# 
# 1. **Retrieval-Augmented Generation (RAG) for Podcast Summaries:**  
#    Combine large language models (LLMs) with data retrieval from Neo4j to generate insightful episode summaries or answer user queries by referencing related content.
# 
# 2. **RAG-Graph for Thematic Exploration:**  
#    Integrate RAG techniques with graph-based search methods to offer context-aware, detailed insights into episodes. This approach can help users navigate complex scientific topics by linking episodes and references seamlessly.
# 
# 3. **Episode Clusterization and Recommendation Systems:**  
#    Apply clustering algorithms on the graph data to identify groups of episodes that share common themes or references. This can power personalized recommendation systems, suggesting episodes similar to those users already enjoy.
# 
# 4. **Pathway Discovery for Thematic Learning:**  
#    Leverage graph analytics to map out learning pathways. For example, if a user is interested in the theme of behavior, the system can highlight a sequential pathway through episodes and references that deepen their understanding of the topic.
# 
# 5. **Interdisciplinary Knowledge Mapping:**  
#    Analyze the intersections of various scientific disciplines across episodes by examining shared references. This can uncover hidden relationships and provide insights into how different fields influence each other.
# 
# The following sections explain how the data is scraped, normalized, and imported into Neo4j, setting the stage for these advanced analyses and applications in future projects.
# 
# 
# For more details about the podcast and its themes, you can check out [Naruhodo on B9](https://www.b9.com.br/shows/naruhodo/).

# %% [markdown]
# <a name="project-structure"></a>
# ## Project Structure
# 
# The repository is organized into the following modules:
# 
# - **Environment Configuration:**  
#   Stores all sensitive connection details (such as Neo4j credentials and file paths) in a `.env` file using `python-dotenv`. This keeps your configuration secure and separate from the code.
# 
# - **Data Scraping Module:**  
#   Contains functions that send HTTP requests, parse HTML content, and extract references from individual podcast posts. This module forms the foundation for gathering raw data from the Naruhodo website.
# 
# - **Data Collection and CSV Generation:**  
#   Iterates over multiple search result pages to collect all podcast post URLs and then scrapes each post for its references. The collected data is saved as a ragged CSV file, where each row contains the episode URL followed by a variable number of reference strings.
# 
# - **CSV Normalization:**  
#   Converts the ragged CSV into a normalized CSV format. In the normalized file, each row represents a single relationship between an episode and one reference, making the data ideal for graph import and subsequent analysis.
# 
# - **Neo4j Data Import:**  
#   Loads the normalized CSV file and builds the graph in Neo4j by creating nodes for episodes and references, and establishing `:REFERENCES` relationships between them. This module lays the groundwork for future graph-based analyses and applications.
# 

# %% [markdown]
# <a name="Environment-and-dependencies"></a>
# ## Environment and Dependencies
# 
# - **Python 3.x**
# - **Dependencies:**
#   - `neo4j-driver`
#   - `python-dotenv`
#   - `pandas` (optional for CSV processing)
#   - `csv` (Python’s built-in module)
# 
# All sensitive configuration values—such as the Neo4j URI, username, and password, as well as the output CSV path—are stored in a single `.env` file that is excluded from version control.

# %% [markdown]
# <a name="Code-breakdown"></a>
# ## Code Breakdown

# %% [markdown]
# <a name="data-scraping-module"></a>
# ### 1. Data Scraping Module
# **`get_soup(url: str) -> BeautifulSoup`**  
#   **Purpose:**  
#   - Sends a GET request to the given URL using custom headers.
#   - Handles HTTP errors and sets the proper encoding.
#   - Returns a BeautifulSoup object for HTML parsing.
# 
# 
# **`extract_references(post_url: str) -> List[str]`**  
#   **Purpose:**  
#   - Fetches the HTML content of a podcast post.
#   - Locates the “REFERÊNCIAS” section and extracts all subsequent reference texts until a delimiter is encountered.
#   - Returns a list of reference strings (or an empty list if no references are found).

# %%
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


# %%
# Example usage:
if __name__ == '__main__':
    # Replace 'your_post_url' with the actual URL you want to scrape.
    your_post_url = 'https://www.b9.com.br/shows/naruhodo/naruhodo-418-o-que-e-a-birra/?highlight=naruhodo'
    refs = extract_references(your_post_url)
    for ref in refs:
        print(ref)
        

# %% [markdown]
# <a name="data-collection-and-csv-generation"></a>
# ### 2. Data Collection and CSV Generation
# **`get_podcast_posts(page_number: int) -> List[str]`**  
#   **Purpose:**  
#   - Constructs the search URL using the page number.
#   - Scrapes the page to extract all podcast post URLs by selecting elements with the CSS class `c-post-card__link`.
# 
# **`scrape_references() -> List[List[str]]`**   
#   **Purpose:**  
#   - Iterates through search result pages starting from page 1 until no more post URLs are found.
#   - For each post URL, calls `extract_references` to collect the references.
#   - Aggregates the data so that each row consists of the post URL followed by its corresponding references.
# 
# **`save_to_csv(data: List[List[str]], filename: str = 'references.csv') -> None`**   
#   **Purpose:**  
#   - Writes the aggregated (ragged) data to a CSV file using UTF-8 encoding.
#   - Each row in the CSV starts with the post URL and is followed by the extracted references.
# 

# %% [markdown]
# TESTE

# %%
import os
import pandas as pd
from dotenv import load_dotenv
from typing import NoReturn, List



# Updated URL format for pages
SEARCH_URL: str = 'https://www.b9.com.br/shows/naruhodo/?pagina={}#anchor-tabs'

def get_podcast_posts(page_number: int) -> List[str]:
    """
    Retrieve podcast post URLs from a search page.

    This function formats the search URL with the provided page number,
    fetches the page content using get_soup, and extracts all post links
    that contain 'naruhodo' in their href using multiple selectors to ensure
    we catch all episodes. Only keeps links from b9.com.br domain.

    Args:
        page_number (int): The page number to scrape.

    Returns:
        List[str]: A list of URLs for the podcast posts found on the page.
    """
    # Format the URL with the given page number and retrieve its parsed content.
    soup = get_soup(SEARCH_URL.format(page_number))
    
    # Find all links using multiple selectors to catch all possible episode links
    all_links = []
    
    # Method 1: Direct link search
    links = soup.find_all('a', href=lambda href: href and 'naruhodo' in href.lower())
    all_links.extend(links)
    
    # Method 2: Search in article titles
    articles = soup.find_all('article')
    for article in articles:
        title_links = article.find_all('a', href=lambda href: href and 'naruhodo' in href.lower())
        all_links.extend(title_links)
    
    # Method 3: Search in post listings
    post_listings = soup.find_all('div', class_='post-listing')
    for listing in post_listings:
        listing_links = listing.find_all('a', href=lambda href: href and 'naruhodo' in href.lower())
        all_links.extend(listing_links)
    
    # Extract unique URLs while preserving order and add base URL if needed
    # Only keep URLs from b9.com.br domain
    seen = set()
    unique_links = []
    for link in all_links:
        href = link['href']
        # Add base URL if the link is relative
        if href.startswith('/'):
            href = f"https://www.b9.com.br{href}"
        
        # Only keep links from b9.com.br domain
        if (href not in seen and 
            'naruhodo' in href.lower() and 
            'b9.com.br' in href.lower() and
            not any(ext in href.lower() for ext in ['podcast.apple', 'facebook', 'twitter', 'spotify', 'youtube'])):
            seen.add(href)
            unique_links.append(href)
    
    print(f"Found {len(unique_links)} unique b9.com.br podcast links on page {page_number}")
    return unique_links

# Updated to iterate from page 1 to 35
def scrape_references() -> List[List[str]]:
    """
    Scrape references from podcast posts across pages 1 to 35.

    Returns:
        List[List[str]]: A list of lists, where each inner list contains a post URL
                         and its corresponding references.
    """
    all_references: List[List[str]] = []
    
    # Iterate from page 1 to 35
    for page in range(21, 36):
        print(f"Scraping page {page} of 35...")
        try:
            post_links = get_podcast_posts(page)
            
            # If no valid Naruhodo episodes are found, log and continue
            if not post_links:
                print(f"No Naruhodo episodes found on page {page}. Continuing to next page.")
                continue
            
            # Process each episode link
            for post_link in post_links:
                print(f"Scraping post {post_link}...")
                try:
                    references = extract_references(post_link)
                    # Prepend the post URL to the list of references.
                    all_references.append([post_link] + references)
                    # Pause for 1-2 seconds to be respectful to the server.
                    time.sleep(random.uniform(1, 2))
                except Exception as e:
                    print(f"Error scraping {post_link}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")
            # Continue to the next page instead of breaking
            continue

    print(f"Scraping completed. Processed {len(all_references)} episodes.")
    return all_references

def save_to_csv(data: List[List[str]], filename: str = 'references3.csv') -> None:
    """
    Save the scraped data to a CSV file with structured columns.
    Each reference will be in its own column (Reference_1, Reference_2, etc.).

    Args:
        data (List[List[str]]): List where each inner list contains [episode_url, reference1, reference2, ...]
        filename (str): Name of the output CSV file
    """
    # Find the maximum number of references in any episode
    max_refs = max(len(row) - 1 for row in data)  # -1 because first element is episode URL
    
    # Create column names
    columns = ['Episode'] + [f'Reference_{i+1}' for i in range(max_refs)]
    
    # Create a list of dictionaries where each dictionary represents a row
    structured_data = []
    for row in data:
        episode_data = {'Episode': row[0]}  # First element is always the episode URL
        
        # Add references to their respective columns
        for i, ref in enumerate(row[1:]):  # Skip the first element (episode URL)
            if ref.strip():  # Only add non-empty references
                episode_data[f'Reference_{i+1}'] = ref.strip()
        
        structured_data.append(episode_data)
    
    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(structured_data, columns=columns)
    
    # Save to CSV, handling missing values properly
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"Saved {len(df)} episodes with up to {max_refs} references each to {filename}")
    print(f"Column names: {', '.join(columns)}")

if __name__ == "__main__":
    # Load environment variables from the .env file (if needed)
    load_dotenv()

# %%
    # Scrape references from the website and save them to a CSV file.
    references = scrape_references()
    save_to_csv(references)
    print("Data has been saved to references.csv")

# %% [markdown]
# <a name="csv-normalization"></a>
# ### 3. CSV Normalization
# **`normalize_references(input_file: str, output_file: str) -> None`**  
#   **Purpose:**  
#   - Reads the ragged CSV (where each row has an episode followed by a variable number of references).
#   - Converts the data into a normalized CSV format with two columns: "Episode" and "Reference".
#   - Each row in the normalized CSV represents one episode–reference relationship.

# %%
import pandas as pd

# Function to process a single file into long format
def process_file_to_long_format(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Melt the dataframe to create a long format
    melted_df = pd.melt(
        df,
        id_vars=['Episode'],
        value_vars=[col for col in df.columns if col.startswith('Reference_')],
        var_name='Reference_Number',
        value_name='Reference'
    )
    
    # Clean up the data
    melted_df = melted_df.dropna(subset=['Reference'])
    melted_df = melted_df.drop('Reference_Number', axis=1)
    melted_df = melted_df[melted_df['Reference'].str.strip() != '']
    
    return melted_df

# Process both files
print("Processing references2.csv...")
df2 = process_file_to_long_format('references2.csv')
print(f"Shape of references2.csv after processing: {df2.shape}")

print("\nProcessing references3.csv...")
df3 = process_file_to_long_format('references3.csv')
print(f"Shape of references3.csv after processing: {df3.shape}")

# Combine the dataframes
combined_df = pd.concat([df2, df3], ignore_index=True)

# Remove any duplicates
combined_df = combined_df.drop_duplicates()

# Sort by episode URL
combined_df = combined_df.sort_values('Episode')

# Display information
print("\nFinal combined dataset:")
print("Shape:", combined_df.shape)
print("\nFirst few rows:")
display(combined_df.head(10))

# Save to a new CSV file
combined_df.to_csv('combined_references_long_format.csv', index=False)
print("\nSaved to combined_references_long_format.csv")

# Display some statistics
print("\nNumber of references per episode:")
print(combined_df.groupby('Episode').size().describe())

# %% [markdown]
# <a name="neo4j-data-import"></a>
# ### 4. Neo4j Data Import
# **`load_data(filename: str = "references.csv") -> List[List[str]]`**  
#   **Purpose:**  
#   - Loads the normalized CSV file and returns the data as a list of rows, where each row is a list of strings.
# 
# **`create_graph(tx: Transaction, data: List[List[str]]) -> None`**  
#   **Purpose:**  
#   - Iterates over each row from the CSV.
#   - For each row, creates (or merges) an Episode node (using the episode URL) and a Reference node (using the reference URL).
#   - Establishes a `:REFERENCES` relationship between the Episode and Reference nodes via Cypher queries.
# 
# **`main() -> None`**  
#   **Purpose:**  
#   - Orchestrates the Neo4j data import process by loading the CSV data, opening a session, executing the transaction to create the graph, and closing the driver.

# %%
pip install neo4j

# %% [markdown]
# ### Data Cleaning

# %%
import pandas as pd
import re
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = 'datasets/'

def clean_and_prepare_datasets():
    logger.info("Loading original dataset...")
    df = pd.read_csv(os.path.join(DATA_DIR, 'combined_references_long_format.csv'))
    logger.info(f"Initial dataset size: {len(df)} rows")

    # --- Basic Cleaning ---
    def clean_text(text):
        if not isinstance(text, str):
            return text
        text = re.sub('^==>', '', text.strip())
        text = text.rstrip('/')
        return text

    df['Episode'] = df['Episode'].apply(clean_text)
    df['Reference'] = df['Reference'].apply(clean_text)

    # Remove "Podcast das Minas" references
    df = df[~df['Reference'].str.contains('Podcast das #Minas|Podcasts das #Minas', na=False, regex=True)]
    logger.info(f"Dataset size after removing 'Podcast das Minas': {len(df)} rows")

    # --- Title/URL Separation ---
    def separate_title_url(text):
        if not isinstance(text, str):
            return pd.Series({'title': None, 'url': None})
        urls = re.findall(r'https?://[^\s]+', text)
        if len(urls) > 0:
            url = urls[0]
            title = text.replace(url, '').strip()
            if not title:
                title = extract_title_from_url(url)
            return pd.Series({'title': title, 'url': url})
        else:
            return pd.Series({'title': text, 'url': None})

    def extract_title_from_url(url):
        match = re.search(r'naruhodo-\d+-(.*?)(?:/|$)', url)
        if match:
            return match.group(1).replace('-', ' ').title()
        return None

    reference_parts = df['Reference'].apply(separate_title_url)
    df['reference_title'] = reference_parts['title']
    df['reference_url'] = reference_parts['url']

    episode_parts = df['Episode'].apply(separate_title_url)
    df['episode_title'] = episode_parts['title']
    df['episode_url'] = episode_parts['url']

    # --- Episode Number Extraction ---
    def extract_episode_number(url):
        if not isinstance(url, str):
            return None
        match = re.search(r'naruhodo-(\d+)', url)
        if match:
            return int(match.group(1))
        return None

    df['episode_number'] = df['episode_url'].apply(extract_episode_number)
    df['referenced_episode_number'] = df['reference_url'].apply(extract_episode_number)

    # --- Reference Type Classification ---
    logger.info("Classifying reference types...")
    def classify_reference(url, title):
        if not isinstance(url, str):
            if isinstance(title, str):
                return 9  # Unknown type for text-only references
            return 9  # Unknown type for invalid references
        url_lower = url.lower()
        if 'b9.com.br/shows/naruhodo' in url_lower:
            return 8  # Episode
        if any(domain in url_lower for domain in ['youtube.com', 'vimeo.com', 'youtu.be']):
            return 1  # Video
        if any(domain in url_lower for domain in ['doi.org', 'sciencedirect.com', 'springer.com', 'ncbi.nlm.nih.gov', 'jstor.org', 'academia.edu']):
            return 2  # Scientific Paper
        if any(domain in url_lower for domain in ['bbc.com', 'cnn.com', 'nytimes.com', 'folha.uol.com.br', 'g1.globo.com']):
            return 3  # News Article
        if any(domain in url_lower for domain in ['twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com']):
            return 5  # Social Media
        if '.edu' in url_lower:
            return 6  # Academic Website
        if '.gov' in url_lower:
            return 7  # Government Website
        return 9  # Unknown type

    df['reference_type_id'] = df.apply(lambda x: classify_reference(x['reference_url'], x['reference_title']), axis=1)

    # --- Create Master Episode Table ---
    logger.info("Creating master episode table...")
    naruhodo_episodes = df[df['episode_number'].notna()][
        ['episode_number', 'episode_title', 'episode_url']
    ].drop_duplicates().sort_values('episode_number')

    # --- Create Episode-to-Episode References Table ---
    logger.info("Creating episode-to-episode references table with titles...")
    episode_refs = df[df['reference_type_id'] == 8].copy()
    naruhodo_episodes_references = episode_refs[['episode_number', 'referenced_episode_number']].dropna()
    naruhodo_episodes_references['episode_number'] = naruhodo_episodes_references['episode_number'].astype(int)
    naruhodo_episodes_references['referenced_episode_number'] = naruhodo_episodes_references['referenced_episode_number'].astype(int)

    # Map episode numbers to titles
    ep_num_to_title = naruhodo_episodes.set_index('episode_number')['episode_title'].to_dict()
    naruhodo_episodes_references['source_episode_title'] = naruhodo_episodes_references['episode_number'].map(ep_num_to_title)
    naruhodo_episodes_references['referenced_episode_title'] = naruhodo_episodes_references['referenced_episode_number'].map(ep_num_to_title)
    naruhodo_episodes_references = naruhodo_episodes_references.rename(columns={'episode_number': 'source_episode_number'})

    # Reorder columns
    naruhodo_episodes_references = naruhodo_episodes_references[
        ['source_episode_number', 'source_episode_title', 'referenced_episode_number', 'referenced_episode_title']
    ]

    # --- Create External References Table ---
    logger.info("Creating external references table and removing any Naruhodo episodes...")
    non_episode_refs = df[df['reference_type_id'] != 8].copy()
    naruhodo_references = non_episode_refs[[
        'episode_number', 'episode_title',
        'reference_title', 'reference_url',
        'reference_type_id'
    ]].dropna(subset=['episode_number'])

    # Remove any rows where reference_url contains Naruhodo episode URL (extra safety)
    naruhodo_in_refs_url = naruhodo_references[naruhodo_references['reference_url'].str.contains('b9.com.br/shows/naruhodo', na=False)]
    if not naruhodo_in_refs_url.empty:
        logger.warning(f"Removing {len(naruhodo_in_refs_url)} Naruhodo episodes from external references by URL.")
        naruhodo_references = naruhodo_references[~naruhodo_references['reference_url'].str.contains('b9.com.br/shows/naruhodo', na=False)]
    else:
        logger.info("No Naruhodo episodes found in external references by URL.")

    # Remove any rows where reference_title contains "Naruhodo" (final safety net)
    naruhodo_in_refs_title = naruhodo_references[naruhodo_references['reference_title'].str.contains('Naruhodo', na=False, case=False)]
    if not naruhodo_in_refs_title.empty:
        logger.warning(f"Removing {len(naruhodo_in_refs_title)} Naruhodo episodes from external references by title.")
        naruhodo_references = naruhodo_references[~naruhodo_references['reference_title'].str.contains('Naruhodo', na=False, case=False)]
    else:
        logger.info("No Naruhodo episodes found in external references by title.")

    # --- Save Datasets ---
    naruhodo_episodes.to_csv(os.path.join(DATA_DIR, 'naruhodo_episodes.csv'), index=False)
    naruhodo_episodes_references.to_csv(os.path.join(DATA_DIR, 'naruhodo_episodes_references.csv'), index=False)
    naruhodo_references.to_csv(os.path.join(DATA_DIR, 'naruhodo_references.csv'), index=False)

    logger.info(f"Saved {len(naruhodo_episodes)} episodes, {len(naruhodo_episodes_references)} episode-to-episode references, and {len(naruhodo_references)} external references.")

    # --- Validation ---
    logger.info("Validating datasets...")
    # Check for any Naruhodo episodes in external references
    naruhodo_in_refs_url = naruhodo_references[naruhodo_references['reference_url'].str.contains('b9.com.br/shows/naruhodo', na=False)]
    naruhodo_in_refs_title = naruhodo_references[naruhodo_references['reference_title'].str.contains('Naruhodo', na=False, case=False)]
    if not naruhodo_in_refs_url.empty or not naruhodo_in_refs_title.empty:
        logger.warning(f"Still found {len(naruhodo_in_refs_url) + len(naruhodo_in_refs_title)} Naruhodo episodes in external references after cleaning!")
    else:
        logger.info("No Naruhodo episodes found in external references. Clean separation achieved.")

    # Check for missing episode references
    missing_episodes = set(naruhodo_episodes_references['referenced_episode_number']) - set(naruhodo_episodes['episode_number'])
    if missing_episodes:
        logger.warning(f"Referenced episodes not found in master table: {missing_episodes}")
    else:
        logger.info("All referenced episodes are present in the master table.")

    logger.info("Data cleaning and preparation complete.")

# Run the cleaning/preparation
clean_and_prepare_datasets()

# %% [markdown]
# ### Data Import to Neo4j

# %%
import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
DATA_DIR = 'datasets/'

def connect_to_neo4j(uri, user, password):
    return GraphDatabase.driver(uri, auth=(user, password))

def clear_database(session):
    logger.info("Clearing existing database...")
    # Drop constraints first
    constraints_query = "SHOW CONSTRAINTS"
    constraints = session.run(constraints_query).data()
    for constraint in constraints:
        constraint_name = constraint['name']
        session.run(f"DROP CONSTRAINT {constraint_name} IF EXISTS")
    # Delete all nodes and relationships
    delete_query = "MATCH (n) DETACH DELETE n"
    session.run(delete_query)
    logger.info("Database cleared successfully!")

def create_constraints(session):
    logger.info("Creating constraints...")
    constraints = [
        "CREATE CONSTRAINT episode_number IF NOT EXISTS FOR (e:Episode) REQUIRE e.episode_number IS UNIQUE",
        "CREATE CONSTRAINT reference_url IF NOT EXISTS FOR (r:Reference) REQUIRE r.url IS UNIQUE"
    ]
    for constraint in constraints:
        session.run(constraint)

def create_episodes(session, episodes_df):
    logger.info("Creating Episode nodes...")
    episodes_df['episode_number'] = episodes_df['episode_number'].astype(int)
    query = """
    UNWIND $episodes AS episode
    MERGE (e:Episode {episode_number: episode.episode_number})
    SET e.title = episode.episode_title,
        e.url = episode.episode_url
    """
    episodes_data = episodes_df.to_dict('records')
    session.run(query, episodes=episodes_data)

def create_references(session, references_df):
    logger.info("Creating Reference nodes (external only)...")
    # Assign unique placeholder to missing/empty URLs
    missing_mask = references_df['reference_url'].isna() | (references_df['reference_url'].astype(str).str.strip() == '')
    num_missing = missing_mask.sum()
    if num_missing > 0:
        logger.warning(f"Assigning 'unknown_reference_url' to {num_missing} references with missing/empty URLs.")
        references_df.loc[missing_mask, 'reference_url'] = [
            f"unknown_reference_url_{i}" for i in references_df[missing_mask].index
        ]
    references_df = references_df.drop_duplicates(subset=['reference_url'])
    query = """
    UNWIND $references AS ref
    MERGE (r:Reference {url: ref.reference_url})
    SET r.title = ref.reference_title,
        r.type_id = ref.reference_type_id
    """
    references_data = references_df.to_dict('records')
    session.run(query, references=references_data)

def create_episode_to_episode_relationships(session, episode_refs_df):
    logger.info("Creating direct Episode-to-Episode REFERENCES relationships...")
    episode_refs_df['source_episode_number'] = episode_refs_df['source_episode_number'].astype(int)
    episode_refs_df['referenced_episode_number'] = episode_refs_df['referenced_episode_number'].astype(int)
    query = """
    UNWIND $relationships AS rel
    MATCH (source:Episode {episode_number: rel.source_episode_number})
    MATCH (target:Episode {episode_number: rel.referenced_episode_number})
    MERGE (source)-[:REFERENCES]->(target)
    """
    relationships_data = episode_refs_df.to_dict('records')
    session.run(query, relationships=relationships_data)

def create_episode_to_reference_relationships(session, references_df):
    logger.info("Creating Episode-to-Reference REFERENCES relationships...")
    # Assign unique placeholder to missing/empty URLs (to match Reference nodes)
    missing_mask = references_df['reference_url'].isna() | (references_df['reference_url'].astype(str).str.strip() == '')
    if missing_mask.sum() > 0:
        references_df.loc[missing_mask, 'reference_url'] = [
            f"unknown_reference_url_{i}" for i in references_df[missing_mask].index
        ]
    references_df['episode_number'] = references_df['episode_number'].astype(int)
    query = """
    UNWIND $references AS ref
    MATCH (e:Episode {episode_number: ref.episode_number})
    MATCH (r:Reference {url: ref.reference_url})
    MERGE (e)-[:REFERENCES]->(r)
    """
    references_data = references_df.to_dict('records')
    session.run(query, references=references_data)

def run_validation_queries(session):
    logger.info("Running validation queries...")
    validations = [
        ("Total Episode nodes", "MATCH (e:Episode) RETURN count(e) as count"),
        ("Total Reference nodes", "MATCH (r:Reference) RETURN count(r) as count"),
        ("Total Episode-to-Episode REFERENCES", "MATCH (e1:Episode)-[:REFERENCES]->(e2:Episode) RETURN count(*) as count"),
        ("Total Episode-to-Reference REFERENCES", "MATCH (e:Episode)-[:REFERENCES]->(r:Reference) RETURN count(*) as count"),
        ("Sample Episode-to-Episode", "MATCH (e1:Episode)-[:REFERENCES]->(e2:Episode) RETURN e1.episode_number, e2.episode_number LIMIT 3"),
        ("Sample Episode-to-Reference", "MATCH (e:Episode)-[:REFERENCES]->(r:Reference) RETURN e.episode_number, r.title, r.url LIMIT 3")
    ]
    for description, query in validations:
        result = session.run(query).data()
        logger.info(f"{description}: {result}")

def import_data():
    try:
        # Load datasets
        logger.info("Loading datasets...")
        episodes_df = pd.read_csv(os.path.join(DATA_DIR, 'naruhodo_episodes.csv'))
        episode_refs_df = pd.read_csv(os.path.join(DATA_DIR, 'naruhodo_episodes_references.csv'))
        references_df = pd.read_csv(os.path.join(DATA_DIR, 'naruhodo_references.csv'))

        logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
        driver = connect_to_neo4j(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        with driver.session() as session:
            confirmation = input("This will delete all existing data in the database. Proceed? (yes/no): ")
            if confirmation.lower() != 'yes':
                logger.info("Import cancelled.")
                return

            clear_database(session)
            create_constraints(session)
            create_episodes(session, episodes_df)
            create_references(session, references_df)
            create_episode_to_episode_relationships(session, episode_refs_df)
            create_episode_to_reference_relationships(session, references_df)
            run_validation_queries(session)
            logger.info("Import completed successfully!")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    if not (NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD):
        raise ValueError("Missing Neo4j connection details in .env file")
    import_data()

# %% [markdown]
# ### First attempt to import transcripts to Neo4j
# It took to long and the embedding seems to not be done.

# %%
import os
import re
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import pandas as pd

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
DATA_DIR = 'datasets/'
TRANSCRIPTS_DIR = 'transcripts/'

# --- Transcript Parsing ---
def parse_transcript_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extract metadata
    meta = {}
    meta_match = re.search(
        r'Title: (.*?)\nURL: (.*?)\nLanguage: (.*?)\nExtracted on: (.*?)\n', content
    )
    if meta_match:
        meta['title'] = meta_match.group(1)
        meta['url'] = meta_match.group(2)
        meta['language'] = meta_match.group(3)
        meta['extracted_on'] = meta_match.group(4)
        ep_num_match = re.search(r'#(\d+)', meta['title'])
        meta['episode_number'] = int(ep_num_match.group(1)) if ep_num_match else None
    else:
        raise ValueError(f"Could not parse transcript metadata in {file_path}.")
    # Extract segments
    segments = []
    for match in re.finditer(r'\[(\d{2}:\d{2})\] (.*?)(?=\n\[|$)', content, re.DOTALL):
        timestamp, text = match.groups()
        text = text.strip()
        if text and not text.lower().startswith('[música'):
            segments.append({
                'timestamp': timestamp,
                'content': text
            })
    logger.info(f"Parsed {len(segments)} segments from transcript {file_path}.")
    return meta, segments

# --- Embedding Model ---
def get_embedding_model():
    logger.info("Loading embedding model...")
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# --- Neo4j Importer ---
class TranscriptImporter:
    def __init__(self, uri, user, password, embedding_model):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.embedding_model = embedding_model

    def close(self):
        self.driver.close()

    def create_vector_index(self, session, dim=384):
        try:
            logger.info("Creating vector index for TranscriptSegment nodes (if not exists)...")
            session.run(f"""
                CREATE VECTOR INDEX transcript_segment_embedding IF NOT EXISTS
                FOR (s:TranscriptSegment)
                ON (s.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {dim},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
            """)
        except Exception as e:
            logger.warning(f"Could not create vector index: {e}")

    def import_transcript(self, meta, segments):
        with self.driver.session() as session:
            # Ensure Episode node exists
            session.run("""
                MERGE (e:Episode {episode_number: $episode_number})
                SET e.title = $title, e.url = $url
            """, {
                'episode_number': meta['episode_number'],
                'title': meta['title'],
                'url': meta['url']
            })
            # Import segments
            for idx, seg in enumerate(segments):
                seg_id = f"{meta['episode_number']}_{seg['timestamp']}"
                embedding = self.embedding_model.encode(seg['content']).tolist()
                session.run("""
                    MERGE (s:TranscriptSegment {id: $id})
                    SET s.episode_number = $episode_number,
                        s.timestamp = $timestamp,
                        s.content = $content,
                        s.embedding = $embedding
                    WITH s
                    MATCH (e:Episode {episode_number: $episode_number})
                    MERGE (e)-[:HAS_SEGMENT]->(s)
                """, {
                    'id': seg_id,
                    'episode_number': meta['episode_number'],
                    'timestamp': seg['timestamp'],
                    'content': seg['content'],
                    'embedding': embedding
                })
            logger.info(f"Imported {len(segments)} segments for episode {meta['episode_number']}.")
            # (Optional) Create vector index
            self.create_vector_index(session, dim=len(embedding))

# --- Main Batch Import Logic ---
if __name__ == "__main__":
    # Load valid episode numbers from naruhodo_episodes.csv
    episodes_df = pd.read_csv(os.path.join(DATA_DIR, 'naruhodo_episodes.csv'))
    valid_episode_numbers = set(episodes_df['episode_number'].astype(int))
    logger.info(f"Loaded {len(valid_episode_numbers)} valid episode numbers.")

    # Prepare embedding model and importer
    model = get_embedding_model()
    importer = TranscriptImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, model)

    # Process all transcript files
    transcript_files = [os.path.join(TRANSCRIPTS_DIR, f) for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.txt')]
    imported, skipped = 0, 0

    try:
        for file_path in transcript_files:
            try:
                meta, segments = parse_transcript_file(file_path)
                ep_num = meta.get('episode_number')
                if ep_num in valid_episode_numbers:
                    importer.import_transcript(meta, segments)
                    imported += 1
                else:
                    logger.warning(f"Skipping transcript {file_path}: episode {ep_num} not in episode list.")
                    skipped += 1
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                skipped += 1
        logger.info(f"Import complete. Imported: {imported}, Skipped: {skipped}")
    finally:
        importer.close()

# %% [markdown]
# ### Test with single episode

# %%
import os
import re
import logging
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import pandas as pd

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
DATA_DIR = 'datasets/'
TRANSCRIPTS_DIR = 'transcripts/'

# --- Transcript Parsing ---
def parse_transcript_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extract metadata
    meta = {}
    meta_match = re.search(
        r'Title: (.*?)\nURL: (.*?)\nLanguage: (.*?)\nExtracted on: (.*?)\n', content
    )
    if meta_match:
        meta['title'] = meta_match.group(1)
        meta['url'] = meta_match.group(2)
        meta['language'] = meta_match.group(3)
        meta['extracted_on'] = meta_match.group(4)
        ep_num_match = re.search(r'#(\d+)', meta['title'])
        meta['episode_number'] = int(ep_num_match.group(1)) if ep_num_match else None
    else:
        raise ValueError(f"Could not parse transcript metadata in {file_path}.")
    # Extract segments
    segments = []
    for match in re.finditer(r'\[(\d{2}:\d{2})\] (.*?)(?=\n\[|$)', content, re.DOTALL):
        timestamp, text = match.groups()
        text = text.strip()
        if text and not text.lower().startswith('[música'):
            segments.append({
                'timestamp': timestamp,
                'content': text
            })
    logger.info(f"Parsed {len(segments)} segments from transcript {file_path}.")
    return meta, segments

# --- Neo4j Batch Importer ---
class BatchTranscriptImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def batch_import_segments(self, episode_number, segments, episode_title, episode_url):
        with self.driver.session() as session:
            start = time.time()
            # Ensure Episode node exists
            session.run("""
                MERGE (e:Episode {episode_number: $episode_number})
                SET e.title = $title, e.url = $url
            """, {
                'episode_number': episode_number,
                'title': episode_title,
                'url': episode_url
            })
            # Prepare segment data (no embeddings yet)
            segment_nodes = [
                {
                    'id': f"{episode_number}_{seg['timestamp']}",
                    'episode_number': episode_number,
                    'timestamp': seg['timestamp'],
                    'content': seg['content']
                }
                for seg in segments
            ]
            # Batch create TranscriptSegment nodes
            session.run("""
                UNWIND $segments AS seg
                MERGE (s:TranscriptSegment {id: seg.id})
                SET s.episode_number = seg.episode_number,
                    s.timestamp = seg.timestamp,
                    s.content = seg.content
            """, {'segments': segment_nodes})
            # Batch create HAS_SEGMENT relationships
            session.run("""
                UNWIND $segments AS seg
                MATCH (e:Episode {episode_number: seg.episode_number})
                MATCH (s:TranscriptSegment {id: seg.id})
                MERGE (e)-[:HAS_SEGMENT]->(s)
            """, {'segments': segment_nodes})
            end = time.time()
            logger.info(f"Batched import of {len(segments)} segments for episode {episode_number} in {end - start:.2f} seconds.")
            print(f"Batched import of {len(segments)} segments for episode {episode_number} in {end - start:.2f} seconds.")

    def batch_update_embeddings(self, episode_number, segments, embedding_model):
        with self.driver.session() as session:
            start = time.time()
            # Prepare data for batch update
            segment_updates = []
            for seg in segments:
                seg_id = f"{episode_number}_{seg['timestamp']}"
                embedding = embedding_model.encode(seg['content']).tolist()
                segment_updates.append({'id': seg_id, 'embedding': embedding})
            # Batch update embeddings
            session.run("""
                UNWIND $updates AS upd
                MATCH (s:TranscriptSegment {id: upd.id})
                SET s.embedding = upd.embedding
            """, {'updates': segment_updates})
            end = time.time()
            logger.info(f"Batched embedding update for {len(segments)} segments of episode {episode_number} in {end - start:.2f} seconds.")
            print(f"Batched embedding update for {len(segments)} segments of episode {episode_number} in {end - start:.2f} seconds.")

# --- Main Test for Episode 420 ---
if __name__ == "__main__":
    # Find the transcript file for episode 420
    transcript_file = None
    for fname in os.listdir(TRANSCRIPTS_DIR):
        if fname.endswith('.txt') and '420' in fname:
            transcript_file = os.path.join(TRANSCRIPTS_DIR, fname)
            break
    if not transcript_file:
        logger.error("Transcript file for episode 420 not found.")
        exit(1)

    # Parse transcript
    t0 = time.time()
    meta, segments = parse_transcript_file(transcript_file)
    t1 = time.time()
    logger.info(f"Parsing time: {t1 - t0:.2f} seconds.")
    print(f"Parsing time: {t1 - t0:.2f} seconds.")

    # Batch import segments (no embeddings)
    importer = BatchTranscriptImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    importer.batch_import_segments(meta['episode_number'], segments, meta['title'], meta['url'])

    # Batch embedding update (separate step)
    t2 = time.time()
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    importer.batch_update_embeddings(meta['episode_number'], segments, model)
    t3 = time.time()
    logger.info(f"Total embedding generation and update time: {t3 - t2:.2f} seconds.")
    print(f"Total embedding generation and update time: {t3 - t2:.2f} seconds.")

    importer.close()

# %% [markdown]
# ### Test with Optimized Import Plan: 1-Minute Chunks, 10 Episodes, 2 in Parallel, Timed

# %%
import os
import re
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from neo4j import GraphDatabase

# --- Setup ---
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
TRANSCRIPTS_DIR = 'transcripts'

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
embedding_model = SentenceTransformer(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

CHUNK_SIZE = 300
CHUNK_OVERLAP = 100

# --- Episodes to Skip ---
SKIP_EPISODES = {129, 130, 131, 7, 18, 23, 26, 28, 37, 39, 41, 44, 48, 49, 50, 54, 57, 67, 70, 73, 76, 84, 85, 90, 92, 97, 99, 100, 104, 112}

# --- Transcript Loader ---
def load_transcript(episode_number):
    # Use regex to match the episode number as a complete token after the underscore
    pattern = re.compile(rf"^Naruhodo _{episode_number}\D")
    transcript_files = [f for f in os.listdir(TRANSCRIPTS_DIR) if pattern.match(f) and f.endswith('.txt')]
    if len(transcript_files) != 1:
        raise FileNotFoundError(f"Expected exactly one transcript file for episode {episode_number}, found: {transcript_files}")
    transcript_path = os.path.join(TRANSCRIPTS_DIR, transcript_files[0])
    print(f"Loading transcript for episode {episode_number}: {transcript_path}")  # Debug print
    segments = []
    timestamp_re = re.compile(r"\[(\d{2}):(\d{2})\] ?(.*)")
    with open(transcript_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            match = timestamp_re.match(line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                text = match.group(3).strip()
                total_seconds = minutes * 60 + seconds
                segments.append((total_seconds, text))
    return segments

# --- Token-based Chunker ---
def chunk_transcript_tokenwise(segments, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP, tokenizer=tokenizer):
    all_text = " ".join([text for _, text in segments])
    tokens = tokenizer(all_text, return_offsets_mapping=True, add_special_tokens=False)
    input_ids = tokens['input_ids']
    offsets = tokens['offset_mapping']
    chunks = []
    chunk_spans = []
    start = 0
    while start < len(input_ids):
        end = min(start + chunk_size, len(input_ids))
        chunk_ids = input_ids[start:end]
        chunk_start_char = offsets[start][0]
        chunk_end_char = offsets[end-1][1] if end-1 < len(offsets) else offsets[-1][1]
        chunk_text = all_text[chunk_start_char:chunk_end_char].strip()
        chunks.append(chunk_text)
        chunk_spans.append((start, end))
        if end == len(input_ids):
            break
        start += chunk_size - overlap
    print(f"Chunked into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    print("First 3 chunk lengths (tokens):", [e-s for s, e in chunk_spans[:3]])
    return chunks

# --- Embedding ---
def generate_embeddings(text_chunks, batch_size=32):
    return embedding_model.encode(text_chunks, batch_size=batch_size, show_progress_bar=True)

# --- Neo4j Driver ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def delete_all_transcript_segments():
    with driver.session() as session:
        session.run("""
            MATCH (s:TranscriptSegment)
            DETACH DELETE s
        """)
        session.run("""
            MATCH ()-[r:HAS_SEGMENT]->()
            DELETE r
        """)

def import_to_neo4j(episode_number, text_chunks, embeddings):
    with driver.session() as session:
        session.run(
            """
            MERGE (e:Episode {episode_number: $episode_number})
            """,
            {"episode_number": episode_number}
        )
        segment_nodes = [
            {
                'id': f"{episode_number}_{i}",
                'episode_number': episode_number,
                'chunk_index': i,
                'text': chunk,
                'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            }
            for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings))
        ]
        session.run(
            """
            UNWIND $segments AS seg
            MERGE (s:TranscriptSegment {id: seg.id})
            SET s.episode_number = seg.episode_number,
                s.chunk_index = seg.chunk_index,
                s.text = seg.text,
                s.embedding = seg.embedding
            """,
            {'segments': segment_nodes}
        )
        session.run(
            """
            UNWIND $segments AS seg
            MATCH (e:Episode {episode_number: seg.episode_number})
            MATCH (s:TranscriptSegment {id: seg.id})
            MERGE (e)-[:HAS_SEGMENT]->(s)
            """,
            {'segments': segment_nodes}
        )

# --- Main Loop for Jupyter ---
# 1. Delete all transcript segments before import
print("Deleting all TranscriptSegment nodes and HAS_SEGMENT relationships...")
delete_all_transcript_segments()
print("Done.")

# 2. Import all transcripts except those in SKIP_EPISODES
all_results = []
episode_numbers = []
for fname in os.listdir(TRANSCRIPTS_DIR):
    match = re.search(r'Naruhodo _(\d+)', fname)
    if match:
        ep_num = int(match.group(1))
        if ep_num in SKIP_EPISODES:
            print(f"Skipping episode {ep_num} (in skip list).")
            continue
        if fname.endswith('.txt'):
            episode_numbers.append(ep_num)
episode_numbers = sorted(set(episode_numbers))

for episode_number in episode_numbers:
    timings = {}
    print(f"\nProcessing Episode {episode_number}...")
    t0 = time.time()
    segments = load_transcript(episode_number)
    t1 = time.time()
    timings['load'] = t1 - t0

    chunks = chunk_transcript_tokenwise(segments, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP, tokenizer=tokenizer)
    t2 = time.time()
    timings['chunk'] = t2 - t1

    embeddings = generate_embeddings(chunks, batch_size=32)
    t3 = time.time()
    timings['embed'] = t3 - t2

    import_to_neo4j(episode_number, chunks, embeddings)
    t4 = time.time()
    timings['import'] = t4 - t3

    timings['total'] = t4 - t0
    all_results.append((episode_number, timings))

    print(f"  Load:   {timings['load']:.2f}s")
    print(f"  Chunk:  {timings['chunk']:.2f}s")
    print(f"  Embed:  {timings['embed']:.2f}s")
    print(f"  Import: {timings['import']:.2f}s")
    print(f"  Total:  {timings['total']:.2f}s")

print("\n=== All Episode Timing Summary ===")
for ep, timings in all_results:
    print(f"Episode {ep}: {timings['total']:.2f}s (Load: {timings['load']:.2f}s, Chunk: {timings['chunk']:.2f}s, Embed: {timings['embed']:.2f}s, Import: {timings['import']:.2f}s)")

driver.close()

# %% [markdown]
# <a name="analytical-possibilities-in-neo4j"></a>
# ## Analytical Possibilities in Neo4j
# Once your data is imported into Neo4j, there are numerous analyses you can perform, including:
# 
# - **Cluster Analysis:**
# Identify clusters or communities of episodes that share many common references, which might indicate similar themes or topics.
# 
# - **Centrality Measures:**
# Calculate metrics like degree centrality to identify which episodes or references are the most influential or central in the network.
# 
# - **Path Analysis:**
# Trace paths between episodes to understand how scientific ideas or themes evolve and interconnect across different episodes.
# 
# - **Thematic Mapping:**
# Explore how different subjects or areas of science intersect by analyzing shared references among episodes.
# 
# - **Content Recommendations:**
# Build recommendation systems that suggest related episodes based on shared references or thematic similarities.
# 

# %% [markdown]
# <a name="conclusion"></a>
# ## Conclusion
# This project showcases a complete pipeline for extracting, normalizing, and importing podcast episode data into a Neo4j graph database. By leveraging environment configuration, data normalization, and robust Neo4j import techniques, you can reveal the hidden connections between episodes and references. This approach not only demonstrates technical proficiency in Python and graph databases but also opens up many avenues for sophisticated data analysis—making it an excellent addition to your portfolio.
# 
# Feel free to explore the code and extend its functionality. Happy coding and graph exploring!


