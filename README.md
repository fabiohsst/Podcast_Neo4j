# Naruhodo Podcast Data Importer

## Introduction
*Naruhodo* is not only a podcast—it’s a curated collection of scientific exploration where episodes often intersect through shared references. **The aim of this project is to scrape and import the available Naruhodo podcast data into Neo4j.** Future projects will build on this dataset to analyze connections, thematic clusters, and learning pathways using LLMs and ML.

## How to Run the Project
1. **Clone the Repository:**

`git clone <repository-url>
cd <repository-directory>`

2. **Set Up a Virtual Environment:**
`python -m venv venv
venv\Scripts\activate  # Windows`

3. **Install Dependencies:**
`pip install -r requirements.txt`

4. **Configure the .env File:**
Create a .env file in the project root with content similar to:

`OUTPUT_CSV_PATH=C:/your/desired/path/processed_references.csv
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password`

5. **Run the Data Importer:**
`python neo4j_importer.py`

6. **Explore Your Graph:**
Open the Neo4j Browser, connect to your database, and start querying the graph to discover interconnections.
