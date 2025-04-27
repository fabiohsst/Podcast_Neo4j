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

DATA_DIR = 'Podcast_Neo4j/data/processed/'

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

    # Remove episodes with "Desafio Naruhodo" in the name
    df = df[~df['Episode'].str.contains('Desafio Naruhodo', na=False, case=False)]
    logger.info(f"Dataset size after removing 'Desafio Naruhodo' episodes: {len(df)} rows")

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