"""Databricks SQL access and Gold-table loaders shared by all pages."""

import os

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient

WAREHOUSE_ID = os.getenv("SQL_WAREHOUSE_ID", "64b2e31b1ee2c8a6")

STATUS_LABELS = {
    "exact_baseline": "Exact match",
    "proposed_match": "Proposed match",
}

SHORT_ID_LENGTH = 8

# Gold tables change only when the pipeline reruns, so keep results for an
# hour. The "Refresh data" button clears the cache on demand.
CACHE_TTL = "1h"


def status_label(status) -> str:
    return STATUS_LABELS.get(status, str(status))


def short_id(entity_id: str) -> str:
    return str(entity_id)[:SHORT_ID_LENGTH]


@st.cache_resource
def _workspace() -> WorkspaceClient:
    return WorkspaceClient()


def query_databricks(sql: str) -> pd.DataFrame:
    response = _workspace().statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="30s",
    )

    if response.status and response.status.state:
        state = str(response.status.state)

        if "FAILED" in state or "CANCELED" in state:
            error_message = (
                response.status.error.message
                if response.status.error
                else f"Query failed with state: {state}"
            )
            raise RuntimeError(error_message)

    if not response.result or not response.result.data_array:
        return pd.DataFrame()

    columns = [column.name for column in response.manifest.schema.columns]

    return pd.DataFrame(response.result.data_array, columns=columns)


def _to_numeric(df: pd.DataFrame, columns) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _to_boolean(df: pd.DataFrame, columns) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = df[column].map(
                lambda value: str(value).lower() == "true" if pd.notna(value) else None
            )
    return df


_MATCH_COLUMNS = """
    entity_id,
    company,
    canonical_address,
    country,
    match_score,
    status,
    provider_a_id,
    provider_b_id,
    provider_a_company,
    provider_b_company,
    provider_a_address,
    provider_b_address,
    provider_a_country,
    provider_b_country,
    street_similarity,
    company_similarity,
    city_match,
    postal_match,
    country_match
"""

_BOOLEAN_COLUMNS = ["city_match", "postal_match", "country_match"]


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_entities() -> pd.DataFrame:
    df = query_databricks(
        f"""
        SELECT {_MATCH_COLUMNS}
        FROM addressresolution.gold.entity_matches
        ORDER BY match_score DESC
        """
    )

    df = _to_numeric(df, ["match_score", "street_similarity", "company_similarity"])
    return _to_boolean(df, _BOOLEAN_COLUMNS)


@st.cache_data(ttl=CACHE_TTL, show_spinner="Loading match details…")
def load_entity_details(entity_id: str) -> pd.DataFrame:
    safe_entity_id = entity_id.replace("'", "''")

    df = query_databricks(
        f"""
        SELECT
            {_MATCH_COLUMNS},
            match_rank,
            provider_a_record_id,
            provider_b_record_id,
            company_levenshtein_similarity,
            street_jaro_winkler_similarity,
            city_jaro_winkler_similarity,
            match_weight,
            resolution_run_id,
            resolved_at
        FROM addressresolution.gold.entity_match_details
        WHERE entity_id = '{safe_entity_id}'
        ORDER BY match_rank
        """
    )

    df = _to_numeric(
        df,
        [
            "match_score",
            "street_similarity",
            "company_similarity",
            "company_levenshtein_similarity",
            "street_jaro_winkler_similarity",
            "city_jaro_winkler_similarity",
            "match_weight",
            "match_rank",
        ],
    )
    return _to_boolean(df, _BOOLEAN_COLUMNS)
