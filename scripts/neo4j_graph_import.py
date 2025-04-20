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