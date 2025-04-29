import os
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Robustly find the transcripts directory
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "transcripts")

# Extract episode numbers and URLs from transcript files
def extract_episode_urls(transcripts_dir):
    episode_url_map = {}
    for fname in os.listdir(transcripts_dir):
        match = re.search(r'Naruhodo _([0-9]+)', fname)
        if match:
            ep_num = int(match.group(1))
            # Try to extract URL from file content
            with open(os.path.join(transcripts_dir, fname), encoding='utf-8') as f:
                for line in f:
                    if 'https://' in line:
                        url = line.strip()
                        episode_url_map[ep_num] = url
                        break
    return episode_url_map

# Get existing episode numbers from Neo4j
def get_existing_episodes(driver):
    with driver.session() as session:
        result = session.run("MATCH (e:Episode) RETURN e.episode_number AS ep_num")
        return {record['ep_num'] for record in result}

# Update URLs in Neo4j for existing episodes only
def update_episode_urls(driver, updates):
    updated_count = 0
    with driver.session() as session:
        for ep_num, url in updates.items():
            session.run(
                "MATCH (e:Episode {episode_number: $ep_num}) SET e.url = $url",
                ep_num=ep_num, url=url
            )
            updated_count += 1
    return updated_count

# Extract episode numbers and titles from transcript files
def extract_episode_titles(transcripts_dir):
    episode_title_map = {}
    skipped = []
    for fname in os.listdir(transcripts_dir):
        match = re.search(r'Naruhodo _([0-9]+)', fname)
        if match:
            ep_num = int(match.group(1))
            with open(os.path.join(transcripts_dir, fname), encoding='utf-8') as f:
                first_line = f.readline()
                if first_line.startswith('Title:'):
                    title = first_line[len('Title:'):].strip()
                    if title:
                        episode_title_map[ep_num] = title
                    else:
                        skipped.append((ep_num, fname, "Empty title"))
                else:
                    skipped.append((ep_num, fname, "No title line"))
    return episode_title_map, skipped

# Update titles in Neo4j for existing episodes only
def update_episode_titles(driver, title_map):
    updated_count = 0
    with driver.session() as session:
        for ep_num, title in title_map.items():
            session.run(
                "MATCH (e:Episode {episode_number: $ep_num}) SET e.title = $title",
                ep_num=ep_num, title=title
            )
            updated_count += 1
    return updated_count

if __name__ == "__main__":
    load_dotenv()
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USER = os.getenv('NEO4J_USER')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    episode_url_map = extract_episode_urls(TRANSCRIPTS_DIR)
    existing_episodes = get_existing_episodes(driver)

    # Print which episodes are in transcripts but missing in Neo4j
    transcript_episodes = set(episode_url_map.keys())
    missing_in_neo4j = transcript_episodes - existing_episodes
    if missing_in_neo4j:
        print(f"Episodes in transcripts but missing in Neo4j (not updated): {sorted(missing_in_neo4j)}")

    updates = {ep: url for ep, url in episode_url_map.items() if ep in existing_episodes}
    updated_count = update_episode_urls(driver, updates)
    
    # --- New logic for updating titles ---
    episode_title_map, skipped_titles = extract_episode_titles(TRANSCRIPTS_DIR)
    title_updates = {ep: title for ep, title in episode_title_map.items() if ep in existing_episodes}
    updated_title_count = update_episode_titles(driver, title_updates)
    # -------------------------------------
    driver.close()
    print(f"Updated URLs for {updated_count} episodes in Neo4j.")
    print(f"Updated titles for {updated_title_count} episodes in Neo4j.")
    if skipped_titles:
        print("\nEpisodes skipped due to missing or malformed titles:")
        for ep_num, fname, reason in skipped_titles:
            print(f"  Episode {ep_num} in file '{fname}': {reason}") 