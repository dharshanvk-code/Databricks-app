# Databricks Entity Resolution App

A Streamlit app deployed through Databricks Apps for exploring entity-resolution results produced by our Altana address deduplication pipeline.

The app reads the Gold and Silver tables and provides an interactive way to inspect resolved entities, compare source records, and understand why two records were classified as duplicates.

## Features

- Presentation page (the app opens here)
- Entity Explorer: browse the Gold table, filter by country, and search by company or address
- Click a Gold row to see every source record merged into it, with the merge reason and match scores
- Genie Agent: ask questions about the Gold table in plain English

## Data Sources

The app currently reads from:

`addressresolution.gold.addresses_deduplicated`: the Gold table, one row per resolved address. The Entity Explorer lists it.

`addressresolution.silver.addresses_deduplication`: every source record with its entity ID and the evidence for each merge. Clicking a Gold row loads the records merged into it from here.

The app is read-only and does not modify Bronze, Silver, matching, or Gold data.

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
pip install -r requirements.txt
```

Then run `streamlit run app.py`.

