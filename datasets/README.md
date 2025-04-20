# Naruhodo Dataset Structure

This directory contains the processed datasets from the Naruhodo podcast references analysis.

## Files Description

### 1. combined_references_long_format.csv
Original dataset containing all references from Naruhodo episodes.
- `Episode`: Source episode URL
- `Reference`: Referenced content (URL or text)

### 2. naruhodo_episodes.csv
Master list of all unique Naruhodo episodes.
- `episode_number`: Unique identifier for each episode
- `episode_title`: Title of the episode
- `episode_url`: URL of the episode

### 3. naruhodo_episodes_references.csv
Contains episode-to-episode references, using data from the master episodes list.
- `source_episode_number`: Episode number making the reference
- `source_episode_title`: Title of the source episode
- `referenced_episode_number`: Episode number being referenced
- `referenced_episode_title`: Title of the referenced episode

### 4. naruhodo_references.csv
Contains external references (non-episode references).
- `episode_number`: Episode number making the reference
- `episode_title`: Title of the episode
- `reference_title`: Title or description of the reference
- `reference_url`: URL of the reference
- `reference_type_id`: Type of reference (foreign key to reference_types)

### 5. reference_types.csv
Classification of reference types.
- `type_id`: Unique identifier for reference type
- `type_name`: Name of the reference type
- `description`: Description of the reference type

## Relationships

```
naruhodo_episodes
    ↑ (master list)
    |
    ├── naruhodo_episodes_references (uses episode_number as foreign key)
    |
    └── naruhodo_references (uses episode_number as foreign key)
            |
            └── reference_types (uses type_id as foreign key)
```

## Reference Types

1. Video (YouTube, Vimeo, etc.)
2. Scientific Paper
3. News Article
4. Book
5. Social Media
6. Academic Website
7. Government Website
8. Episode
9. Unknown

## Data Quality Notes

- All episode numbers in naruhodo_episodes_references match entries in naruhodo_episodes
- Episode titles are consistent across all tables
- URLs have been cleaned and validated
- Reference types are standardized 