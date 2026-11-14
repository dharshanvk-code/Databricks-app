"""Databricks SQL access and the Gold/Silver loaders shared by all pages."""

import os

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem

WAREHOUSE_ID = os.getenv("SQL_WAREHOUSE_ID", "64b2e31b1ee2c8a6")

# Gold tables change only when the pipeline reruns, so keep results for an
# hour. The "Refresh data" button clears the cache on demand.
CACHE_TTL = "1h"


@st.cache_resource
def workspace() -> WorkspaceClient:
    return WorkspaceClient()


def query_databricks(sql: str, params: dict[str, str] | None = None) -> pd.DataFrame:
    """Run SQL on the warehouse. Pass values via `params` (`:name` markers),
    never by formatting them into the SQL text."""
    response = workspace().statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        parameters=[
            StatementParameterListItem(name=name, value=value, type="STRING")
            for name, value in (params or {}).items()
        ]
        or None,
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


GOLD_TABLE = "addressresolution.gold.addresses_deduplicated"
# Silver keeps every source record with its entity ID and the evidence for
# each merge. Gold has one canonical row per entity.
SILVER_TABLE = "addressresolution.silver.addresses_deduplication"


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_gold() -> pd.DataFrame:
    return query_databricks(
        f"""
        SELECT company, street_address, city, state, country, provider, provider_id
        FROM {GOLD_TABLE}
        -- Random order, so the explorer opens on a mixed sample. The cache
        -- keeps it the same for an hour.
        ORDER BY rand()
        """
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_merge(provider: str, provider_id: str) -> pd.DataFrame:
    """All Silver records merged into the Gold row (provider, provider_id).
    The canonical record comes first. JSON columns hold the merge evidence."""
    df = query_databricks(
        f"""
        WITH canonical AS (
            SELECT entity_id
            FROM {SILVER_TABLE}
            WHERE provider = :provider AND provider_id = :provider_id
              AND is_canonical
        )
        SELECT
            s.record_id,
            s.provider,
            s.provider_id,
            s.company,
            s.street_address,
            s.city,
            s.state,
            s.country,
            s.entity_id,
            s.is_canonical,
            s.deduplication_status,
            s.cluster_record_count,
            s.merge_authority,
            s.filled_field,
            s.filled_from_record_id,
            s.resolved_at,
            to_json(s.deduplication_steps) AS steps_json,
            to_json(s.deduplication_reasons) AS reasons_json,
            to_json(s.deduplication_evidence) AS evidence_json
        FROM {SILVER_TABLE} s
        JOIN canonical c ON s.entity_id = c.entity_id
        ORDER BY s.is_canonical DESC, s.provider, s.provider_id
        """,
        params={"provider": str(provider), "provider_id": str(provider_id)},
    )
    if not df.empty:
        df["is_canonical"] = df["is_canonical"].map(lambda v: str(v).lower() == "true")
    return df
