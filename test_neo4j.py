from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

print("NEO4J_URI:", os.getenv('NEO4J_URI'))
print("NEO4J_USER:", os.getenv('NEO4J_USER'))
print("NEO4J_PASSWORD:", os.getenv('NEO4J_PASSWORD'))

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

print("Connecting to Neo4j...", flush=True)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
try:
    with driver.session() as session:
        result = session.run("RETURN 1")
        print("Connection successful! Result:", result.single()[0], flush=True)
except Exception as e:
    print("Connection failed:", e, flush=True)
finally:
    driver.close()