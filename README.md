# Naruhodo Podcast Graph Database

**Naruhodo** is a Brazilian podcast dedicated to answering listeners' questions about science, common sense, and curiosities. This project scrapes, processes, and imports Naruhodo podcast data into a Neo4j graph database, enabling advanced analysis and future machine learning applications.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Environment & Dependencies](#environment--dependencies)
- [Scripts & Modules](#scripts--modules)
  - [Data Scraping (`scripts/scrape.py`)](#data-scraping-scriptsscrapepy)
  - [Reference Collection (`scripts/collect_references.py`)](#reference-collection-scriptscollect_referencespy)
  - [CSV Normalization & Cleaning (`scripts/normalize_and_clean.py`)](#csv-normalization--cleaning-scriptsnormalize_and_cleanpy)
  - [Neo4j Graph Import (`scripts/neo4j_graph_import.py`)](#neo4j-graph-import-scriptsneo4j_graph_importpy)
  - [Transcript Embedding (`scripts/transcript_embedding.py`)](#transcript-embedding-scriptstranscript_embeddingpy)
  - [Utilities (`scripts/utils.py`)](#utilities-scriptsutilspy)
- [Datasets](#datasets)
- [Transcripts](#transcripts)
- [Future Directions](#future-directions)

---

## Project Overview
This repository provides a robust pipeline for collecting, cleaning, and importing podcast episode and reference data into a Neo4j graph database. The modular structure supports easy maintenance, testing, and future expansion (e.g., LLMs, recommendations, knowledge graphs).

## Project Structure
```
Podcast_Neo4j/
│
├── data/                   # Project data (see subfolders)
│   ├── raw/                # Raw input data (e.g., scraped CSVs)
│   └── processed/          # Cleaned/normalized data for analysis/import
│
├── documentation/          # Project documentation and reference notebooks
│   ├── data_extraction_import_neo4j.ipynb
│   └── transcript_import_performance_comparison.txt
│
├── queries/                # Query results and analysis CSVs
│   ├── duplicated_segments.csv
│   ├── duplicated_segments_after.csv
│   ├── n_duplicated_segments.csv
│   └── n_duplicated_segments_after.csv
│
├── scripts/                # Python scripts for all processing steps
│   ├── collect_references.py           # Collect podcast post URLs and references
│   ├── data_cleaning.py                # Data cleaning and preparation
│   ├── episodes_transcriptions_retrieve.py # Retrieve and process YouTube transcripts
│   ├── neo4j_graph_import.py           # Neo4j import and graph creation
│   ├── normalize_data.py               # CSV normalization utilities
│   ├── scrape.py                       # Data scraping functions
│   ├── transcript_embedding.py         # Transcript parsing and embedding
│
├── transcripts/            # Transcript files for each episode
│   └── ...
│
├── legacy/                 # Old or superseded scripts and files kept for reference
│   └── data_extraction_markdown.py     # Exported notebook as script (legacy)
│
├── .env                    # Environment variables (Neo4j credentials, etc.)
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation (this file)
├── requirements.txt        # Python dependencies
└── 
```
*Note: Files and folders listed in .gitignore (e.g., venv/, .venv/, __pycache__/, .ipynb_checkpoints) are not shown in this structure.*

## Environment & Dependencies
- Python 3.x
- Install dependencies with:
  ```bash
  pip install -r requirements.txt
  ```
- Store sensitive config (Neo4j URI, credentials, etc.) in `.env` (excluded from version control).

## Scripts & Modules

### collect_references.py
[View script](scripts/collect_references.py)
- Extracts references from individual podcast episode pages on the B9 website.
- Includes functions to fetch HTML, locate the references section, and parse all references for a given episode.

### scrape.py
[View script](scripts/scrape.py)
- Scrapes podcast episode URLs from the B9 website across multiple pages.
- Aggregates all episode links, extracts references, and saves the results to a structured CSV file.

### normalize_data.py
[View script](scripts/normalize_data.py)
- Converts wide-format reference CSVs into a normalized long format suitable for further processing.
- Combines, deduplicates, and sorts reference data from multiple sources.

### data_cleaning.py
[View script](scripts/data_cleaning.py)
- Cleans and prepares the combined references dataset for analysis and import.
- Handles text cleaning, title/URL separation, episode number extraction, reference type classification, and outputs master tables for episodes, episode-to-episode references, and external references.

### neo4j_graph_import.py
[View script](scripts/neo4j_graph_import.py)
- Imports cleaned data into a Neo4j graph database.
- Handles database connection, constraint creation, node and relationship creation, and validation queries.

### episodes_transcriptions_retrieve.py
[View script](scripts/episodes_transcriptions_retrieve.py)
- Downloads and processes YouTube transcripts for podcast episodes.
- Extracts video URLs from a playlist, retrieves transcripts (including auto-generated), and saves them in a structured format.

### transcript_embedding.py
[View script](scripts/transcript_embedding.py)
- Processes transcript text files, chunks and embeds them using a transformer model.
- Imports transcript segments and their embeddings into Neo4j, linking them to the appropriate episode nodes.

## Datasets
- Place raw reference CSVs in the `data/raw/` directory.
- Place cleaned and processed CSVs in the `data/processed/` directory.
- Scripts such as `normalize_data.py` and `data_cleaning.py` will read from and write to these folders as part of the data pipeline.

## Transcripts
- Place transcript text files for each episode in the `transcripts/` directory.
- Scripts like `episodes_transcriptions_retrieve.py` and `transcript_embedding.py` will read from and write to this folder.

## Future Directions
- Retrieval-Augmented Generation (RAG) for podcast summaries
- Thematic exploration and recommendations
- Pathway discovery for thematic learning
- Interdisciplinary knowledge mapping

---

For more details about the podcast, visit [Naruhodo on B9](https://www.b9.com.br/shows/naruhodo/).