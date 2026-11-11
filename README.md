cat > README.md <<'EOF'
# Databricks Entity Resolution App

A Streamlit app deployed through Databricks Apps for exploring entity-resolution results produced by our Altana address deduplication pipeline.

The app connects directly to curated Gold-layer views and provides an interactive way to inspect resolved entities, compare source records, and understand why two records were classified as duplicates.

## Features

- View resolved entities from the Gold layer
- Filter entities by country and match status
- Inspect overall match scores
- Compare Provider A and Provider B records side by side
- View match-explanation signals such as:
  - Street similarity
  - Company similarity
  - City match
  - Country match
- Inspect entities with multiple matched pairs
- Read the latest completed entity-resolution results through Gold views

## Data Sources

The app currently reads from:

`addressresolution.gold.entity_matches`

`addressresolution.gold.entity_match_details`

`entity_matches` provides the main entity-level view used by the application.

`entity_match_details` provides pair-level details for a selected entity, including source records and similarity signals used to explain the match.

The app is read-only and does not modify Bronze, Silver, matching, or Gold data.

## Current Scope

The current Gold views primarily expose high-confidence cross-provider matches between Provider A and Provider B.

Because most accepted matches currently have very high confidence, many displayed match scores are close to or equal to 100%.

Future versions may also expose:

- Provider A ↔ Provider A duplicates
- Provider B ↔ Provider B duplicates
- Lower-confidence matches
- Review and uncertain candidates

The app can then be extended to display these additional entity-resolution cases.

## Architecture

Provider A / Provider B  
↓  
Bronze Ingestion  
↓  
Silver Cleaning & Translation  
↓  
Entity Resolution / Matching  
↓  
Gold Views  
↓  
Databricks App  

The matching pipeline calculates entity relationships and similarity scores. The Gold layer provides stable application-facing views, and the Streamlit app visualizes those results.

## Tech Stack

- Databricks
- Databricks Apps
- Databricks SQL
- Unity Catalog
- Streamlit
- Python
- Pandas
- Databricks SDK

## Running Locally

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt# Databricks-app
