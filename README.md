# Naruhodo References - Knowledge Graph & AI-Powered Exploration

## About the Project

This project builds a knowledge graph and AI-powered exploration system for the **Naruhodo** podcast, a Brazilian show dedicated to answering science questions and exploring curiosities. The system creates a comprehensive database of episodes, references, and transcript segments using Neo4j as a graph database.

The project includes:
- Data extraction from the podcast website
- Transcript processing from YouTube videos
- Neo4j graph database implementation
- Vector embeddings for semantic search
- A GraphRAG (Retrieval Augmented Generation) system for AI-powered exploration

## 🚀 Quick Start

1. **Setup your environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your environment**
   Create a `.env` file with:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=yourpassword
   OPENAI_API_KEY=your_openai_key
   ```

3. **Run the GraphRAG chatbot**
   ```bash
   streamlit run GraphRAG/chatbot_streamlit.py
   ```

## 📊 Data Pipeline

The project implements a complete data pipeline:

1. **Data Collection**
   - Website scraping (`scripts/scrape.py`)
   - Reference extraction (`scripts/collect_references.py`)
   - YouTube transcript retrieval (`scripts/episodes_transcriptions_retrieve.py`)

2. **Data Processing**
   - Data normalization (`scripts/normalize_data.py`)
   - Data cleaning and transformation (`scripts/data_cleaning.py`)
   - Transcript chunking and embedding (`scripts/transcript_embedding.py`)

3. **Knowledge Graph**
   - Neo4j import and graph creation (`scripts/neo4j_graph_import.py`)
   - Similarity relationships (`scripts/create_similar_to_relationships.py`)

4. **AI Integration**
   - GraphRAG implementation (`GraphRAG/` directory)
   - LLM integration with OpenAI models (`GraphRAG/llm_integration.py`)
   - Context-aware retrieval (`GraphRAG/retrieval_layer.py`, `GraphRAG/context_builder.py`)

## 📚 Knowledge Graph Structure

The graph database includes:
- **Episode** nodes: Podcast episodes with metadata
- **Reference** nodes: External references mentioned in episodes
- **Segment** nodes: Transcript segments with vector embeddings
- **Relationships**:
  - `REFERENCES`: Episodes referencing other episodes or external sources
  - `HAS_SEGMENT`: Episodes to transcript segments
  - `SIMILAR_TO`: Semantic similarity between segments/episodes

## 🤖 GraphRAG System

The GraphRAG system combines graph traversal and retrieval-augmented generation:

- **Retrieval Layer**: Finds relevant content through vector similarity and graph paths
- **Context Builder**: Constructs contextual prompts from retrieved information
- **LLM Integration**: Powers the system with OpenAI's models
- **User Interface**: Streamlit-based interactive chatbot

### Key Features
- Semantic search across transcripts
- Context-aware responses based on podcast knowledge
- Cross-episode knowledge exploration
- Thematic traversal through related content

## 📂 Project Structure

```
Podcast_Neo4j/
│
├── GraphRAG/                # RAG implementation
│   ├── chatbot_streamlit.py # Streamlit interface
│   ├── chatbot_interface.py # Alternative interface
│   ├── retrieval_layer.py   # Knowledge retrieval system
│   ├── context_builder.py   # LLM prompt construction
│   ├── llm_integration.py   # OpenAI API integration
│   └── test_*.py            # Testing modules
│
├── data/                    # Data storage
│   ├── raw/                 # Raw scraped data
│   └── processed/           # Processed data files
│
├── documentation/           # Project documentation
│
├── scripts/                 # Processing scripts
│   ├── scrape.py                       # Website scraping
│   ├── collect_references.py           # Reference extraction
│   ├── episodes_transcriptions_retrieve.py # YouTube transcript retrieval
│   ├── normalize_data.py               # Data normalization
│   ├── data_cleaning.py                # Data cleaning
│   ├── neo4j_graph_import.py           # Neo4j import
│   ├── transcript_embedding.py         # Text embedding
│   └── create_similar_to_relationships.py # Similarity creation
│
├── transcripts/             # Episode transcript files
│
├── images/                  # Project images and diagrams
│
└── requirements.txt         # Project dependencies
```

## 🧰 Technologies

- **Database**: Neo4j (Graph database)
- **Machine Learning**: Sentence-Transformers (Vector embeddings)
- **AI**: OpenAI's models (GPT-based LLM integration)
- **Data Processing**: Python, Pandas
- **Web Interface**: Streamlit
- **Web Scraping**: Beautiful Soup, Requests

## 🔮 Future Directions

- Enhanced question answering with citations
- Semantic pathway discovery for topic exploration
- Content recommendation based on user interests
- Interdisciplinary knowledge mapping
- Integration with other knowledge sources

## 📝 License

This project is for educational and research purposes only. All podcast content belongs to its original creators.

---

For more information about the podcast, visit [Naruhodo on B9](https://www.b9.com.br/shows/naruhodo/).