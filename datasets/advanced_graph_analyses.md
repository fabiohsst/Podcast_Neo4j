# Advanced Analyses for the Naruhodo Podcast Knowledge Graph

## 1. Network Centrality & Influence
- **Most Influential Episodes:** Find episodes referenced by the most other episodes (in-degree centrality).
- **Hub Episodes:** Find episodes that reference many others (out-degree centrality).
- **Betweenness Centrality:** Identify episodes that act as bridges between different clusters or topics.

## 2. Reference Pathways & Citation Chains
- **Reference Chains:** Find chains of references (e.g., Episode A references B, which references C).
- **Cycles:** Detect if there are any cycles (e.g., A references B, B references C, C references A).
- **Shortest Path:** Find the shortest reference path between two episodes (useful for tracing influence or topic flow).

## 3. Community Detection & Clustering
- **Episode Communities:** Use algorithms (like Louvain or Label Propagation) to find clusters of episodes that frequently reference each other—these may represent thematic series or recurring topics.
- **Reference Clusters:** Group external references that are cited by similar sets of episodes.

## 4. Temporal Analysis
- **Reference Trends Over Time:** Analyze how referencing behavior changes across episode numbers (e.g., do later episodes reference earlier ones more?).
- **Emergence of Topics:** Track when certain types of references (e.g., scientific papers, news articles) become more common.

## 5. Content & Topic Analysis
- **Topic Propagation:** If you have transcripts or tags, see how topics propagate through references.
- **Reference Diversity:** Measure how diverse the sources are for each episode (e.g., does an episode cite only internal episodes, or a mix of external sources?).

## 6. Cross-Modal Analysis
- **Reference Type Impact:** Analyze whether episodes that cite more scientific papers are more likely to be referenced by others.
- **Reference Co-occurrence:** Find pairs of references (internal or external) that are often cited together.

## 7. GraphRAG and Semantic Search
- **Semantic Retrieval:** Use embeddings to find transcript segments or references most relevant to a query, then expand to related episodes or references.
- **Contextual Q&A:** Given a question, retrieve the most relevant episodes, references, and their connections for context-aware answers.

## 8. Visualization
- **Subgraph Extraction:** Visualize the reference network for a given episode or topic.
- **Ego Networks:** Show all direct and indirect references for a single episode.

## 9. Data Quality & Integrity Checks
- **Orphan Nodes:** Find references or episodes not connected to the main graph.
- **Dangling References:** Detect references to episodes that do not exist in the master list.

## 10. Custom Analytics
- **Reference Lifespan:** How long does an episode continue to be referenced after its release?
- **Reference Recurrence:** Are there references (internal or external) that are repeatedly cited across many episodes?

---

### Example Advanced Cypher Queries

- **Find the shortest reference path between two episodes:**
  ```cypher
  MATCH p = shortestPath(
    (e1:Episode {episode_number: 10})-[:REFERENCES*..5]->(e2:Episode {episode_number: 42})
  )
  RETURN p
  ```

- **Find clusters of episodes (community detection):**
  ```cypher
  CALL gds.louvain.stream({
    nodeProjection: 'Episode',
    relationshipProjection: {
      REFERENCES: {
        type: 'REFERENCES',
        orientation: 'UNDIRECTED'
      }
    }
  })
  YIELD nodeId, communityId
  RETURN gds.util.asNode(nodeId).episode_number AS episode, communityId
  ORDER BY communityId
  ``` 