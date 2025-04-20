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
├── data/                   # Raw and processed data (CSV, transcripts, etc.)
│   ├── raw/
│   ├── processed/
│
├── notebooks/              # Jupyter notebooks for exploration and documentation
│   └── data_extraction_import_neo4j.ipynb
│
├── scripts/                # Python scripts for modularized code
│   ├── scrape.py                   # Data scraping functions
│   ├── collect_references.py       # Collect podcast post URLs and references
│   ├── normalize_and_clean.py      # CSV normalization and cleaning
│   ├── neo4j_graph_import.py       # Neo4j import and graph creation
│   ├── transcript_embedding.py     # Transcript parsing and embedding
│   └── utils.py                    # Shared utility functions
│
├── datasets/               # Reference CSVs
├── transcripts/            # Transcript files
├── .env                    # Environment variables (Neo4j credentials, etc.)
├── requirements.txt        # Python dependencies
├── README.md
└── 
```

## Environment & Dependencies
- Python 3.x
- Install dependencies with:
  ```bash
  pip install -r requirements.txt
  ```
- Store sensitive config (Neo4j URI, credentials, etc.) in `.env` (excluded from version control).

## Scripts & Modules

### Data Scraping (`scripts/scrape.py`)
[View script](scripts/scrape.py)
- Functions to send HTTP requests, parse HTML, and extract references from podcast posts.

### Reference Collection (`scripts/collect_references.py`)
[View script](scripts/collect_references.py)
- Collects all podcast post URLs, scrapes references, and saves to CSV.

### CSV Normalization & Cleaning (`scripts/normalize_and_clean.py`)
[View script](scripts/normalize_and_clean.py)
- Cleans and normalizes CSVs for graph import.

### Neo4j Graph Import (`scripts/neo4j_graph_import.py`)
[View script](scripts/neo4j_graph_import.py)
- Loads normalized CSV, builds graph in Neo4j, creates nodes and relationships.

### Transcript Embedding (`scripts/transcript_embedding.py`)
[View script](scripts/transcript_embedding.py)
- Parses transcript files, generates embeddings, and imports transcript data into Neo4j.

### Utilities (`scripts/utils.py`)
[View script](scripts/utils.py)
- Shared helper functions used across modules.

## Datasets
- Place reference CSVs in the `datasets/` directory.

## Transcripts
- Place transcript files in the `transcripts/` directory.

## Future Directions
- Retrieval-Augmented Generation (RAG) for podcast summaries
- Thematic exploration and recommendations
- Pathway discovery for thematic learning
- Interdisciplinary knowledge mapping

---

For more details about the podcast, visit [Naruhodo on B9](https://www.b9.com.br/shows/naruhodo/).
