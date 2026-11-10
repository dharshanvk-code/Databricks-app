import os
import pandas as pd
import streamlit as st

from databricks.sdk import WorkspaceClient


st.set_page_config(
    page_title="Altana Entity Resolution",
    layout="wide"
)


# -------------------------------------------------
# DATABRICKS CONNECTION
# -------------------------------------------------

warehouse_id = os.getenv(
    "SQL_WAREHOUSE_ID",
    "64b2e31b1ee2c8a6"
)

workspace = WorkspaceClient()


def query_databricks(sql: str) -> pd.DataFrame:
    response = workspace.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="30s"
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

    columns = [
        column.name
        for column in response.manifest.schema.columns
    ]

    return pd.DataFrame(
        response.result.data_array,
        columns=columns
    )


# -------------------------------------------------
# DATA HELPERS
# -------------------------------------------------

def convert_numeric_columns(df: pd.DataFrame, columns):
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def convert_boolean_columns(df: pd.DataFrame, columns):
    for column in columns:
        if column in df.columns:
            df[column] = df[column].map(
                lambda value: (
                    str(value).lower() == "true"
                    if pd.notna(value)
                    else None
                )
            )

    return df


# -------------------------------------------------
# LOAD ENTITY LIST
# -------------------------------------------------

@st.cache_data(ttl=60)
def load_entities():
    sql = """
    SELECT
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
    FROM addressresolution.gold.entity_matches
    ORDER BY match_score DESC
    """

    df = query_databricks(sql)

    df = convert_numeric_columns(
        df,
        [
            "match_score",
            "street_similarity",
            "company_similarity"
        ]
    )

    df = convert_boolean_columns(
        df,
        [
            "city_match",
            "postal_match",
            "country_match"
        ]
    )

    return df


# -------------------------------------------------
# LOAD ENTITY DETAILS
# -------------------------------------------------

@st.cache_data(ttl=60)
def load_entity_details(entity_id: str):
    safe_entity_id = entity_id.replace("'", "''")

    sql = f"""
    SELECT
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
        country_match,
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

    df = query_databricks(sql)

    df = convert_numeric_columns(
        df,
        [
            "match_score",
            "street_similarity",
            "company_similarity",
            "company_levenshtein_similarity",
            "street_jaro_winkler_similarity",
            "city_jaro_winkler_similarity",
            "match_weight",
            "match_rank"
        ]
    )

    df = convert_boolean_columns(
        df,
        [
            "city_match",
            "postal_match",
            "country_match"
        ]
    )

    return df


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

try:
    df = load_entities()

except Exception as error:
    st.error("Unable to load Gold entity data.")
    st.exception(error)

    st.info(
        "If you are running locally, Databricks authentication "
        "must also be configured on your machine. "
        "The deployed Databricks App authenticates automatically."
    )

    st.stop()


# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.title("Altana Entity Resolution")

st.caption(
    "Explore resolved entities, review matches, "
    "and understand why records were deduplicated."
)


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.header("Entity Resolution Agent")

    question = st.text_input(
        "Ask about the data",
        placeholder="Why was this entity matched?"
    )

    if question:
        q = question.lower()

        if "matched" in q and "how many" in q:
            st.success(
                f"There are {len(df):,} resolved entities."
            )

        elif "under 85" in q or "below 85" in q:
            low_confidence = df[
                df["match_score"] < 0.85
            ]

            if low_confidence.empty:
                st.info(
                    "There are no matches below 85%."
                )
            else:
                st.dataframe(
                    low_confidence[
                        [
                            "entity_id",
                            "company",
                            "match_score",
                            "status"
                        ]
                    ],
                    hide_index=True
                )

        else:
            st.info(
                "Try asking:\n\n"
                "- How many are matched?\n"
                "- Show matches under 85%"
            )

    st.divider()

    status_options = sorted(
        df["status"]
        .dropna()
        .unique()
        .tolist()
    )

    status_filter = st.multiselect(
        "Status",
        options=status_options,
        default=status_options
    )

    country_options = sorted(
        df["country"]
        .dropna()
        .unique()
        .tolist()
    )

    country_filter = st.multiselect(
        "Country",
        options=country_options
    )


# -------------------------------------------------
# FILTER DATA
# -------------------------------------------------

filtered_df = df[
    df["status"].isin(status_filter)
].copy()

if country_filter:
    filtered_df = filtered_df[
        filtered_df["country"].isin(
            country_filter
        )
    ]


# -------------------------------------------------
# SUMMARY METRICS
# -------------------------------------------------

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric(
        "Entities",
        f"{len(filtered_df):,}"
    )

with metric_2:
    exact_matches = len(
        filtered_df[
            filtered_df["status"] == "exact_baseline"
        ]
    )

    st.metric(
        "Exact Matches",
        f"{exact_matches:,}"
    )

with metric_3:
    proposed_matches = len(
        filtered_df[
            filtered_df["status"] == "proposed_match"
        ]
    )

    st.metric(
        "Proposed Matches",
        f"{proposed_matches:,}"
    )

with metric_4:
    if len(filtered_df) > 0:
        average_score = (
            filtered_df["match_score"].mean()
            * 100
        )

        st.metric(
            "Avg. Match Score",
            f"{average_score:.1f}%"
        )
    else:
        st.metric(
            "Avg. Match Score",
            "—"
        )


# -------------------------------------------------
# ENTITY TABLE
# -------------------------------------------------

st.subheader("Resolved Entities")

st.caption(
    "Select a row to inspect all matched records "
    "for that entity."
)

display_df = filtered_df[
    [
        "entity_id",
        "company",
        "canonical_address",
        "country",
        "match_score",
        "status"
    ]
].copy()

display_df["match_score"] = (
    display_df["match_score"]
    * 100
).round(1)

display_df = display_df.rename(
    columns={
        "entity_id": "Entity ID",
        "company": "Company",
        "canonical_address": "Canonical Address",
        "country": "Country",
        "match_score": "Match Score (%)",
        "status": "Status"
    }
)

if display_df.empty:
    st.warning(
        "No entities match the selected filters."
    )
    st.stop()


event = st.dataframe(
    display_df,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="entity_table"
)

selected_rows = event.selection.rows

if selected_rows:
    selected_index = selected_rows[0]
else:
    selected_index = 0

selected_entity = filtered_df.iloc[
    selected_index
]["entity_id"]


# -------------------------------------------------
# DETAIL QUERY
# -------------------------------------------------

try:
    detail_df = load_entity_details(
        selected_entity
    )

except Exception as error:
    st.error(
        "Unable to load entity match details."
    )

    st.exception(error)
    st.stop()


if detail_df.empty:
    st.warning(
        "No match details found for this entity."
    )
    st.stop()


best_match = detail_df.iloc[0]


# -------------------------------------------------
# MATCH EXPLANATION
# -------------------------------------------------

st.divider()

st.subheader(
    f"Entity {selected_entity} — Match Explanation"
)

score_col, decision_col, company_col = st.columns(3)

with score_col:
    st.metric(
        "Overall Match Score",
        f"{best_match['match_score'] * 100:.0f}%"
    )

with decision_col:
    decision = best_match["status"]

    if decision == "exact_baseline":
        decision_display = "Exact Match"

    elif decision == "proposed_match":
        decision_display = "Duplicate"

    else:
        decision_display = str(decision)

    st.metric(
        "Decision",
        decision_display
    )

with company_col:
    st.metric(
        "Canonical Company",
        best_match["company"]
    )


# -------------------------------------------------
# MULTIPLE MATCHES
# -------------------------------------------------

if len(detail_df) > 1:
    st.info(
        f"This entity has {len(detail_df)} "
        "matched Provider A ↔ Provider B pairs."
    )

    match_options = []

    for _, row in detail_df.iterrows():
        match_options.append(
            f"Match {int(row['match_rank'])}: "
            f"A-{row['provider_a_id']} ↔ "
            f"B-{row['provider_b_id']} "
            f"({row['match_score'] * 100:.1f}%)"
        )

    selected_match_label = st.selectbox(
        "Matched pair",
        match_options
    )

    selected_match_index = match_options.index(
        selected_match_label
    )

    selected_match = detail_df.iloc[
        selected_match_index
    ]

else:
    selected_match = detail_df.iloc[0]


# -------------------------------------------------
# SOURCE RECORDS
# -------------------------------------------------

st.write("### Source Records")

provider_a_col, provider_b_col = st.columns(2)

with provider_a_col:
    st.write("#### Provider A")

    st.write(
        f"**Record ID:** "
        f"{selected_match['provider_a_id']}"
    )

    st.write(
        f"**Company:** "
        f"{selected_match['provider_a_company']}"
    )

    st.write(
        f"**Address:** "
        f"{selected_match['provider_a_address']}"
    )

    st.write(
        f"**Country:** "
        f"{selected_match['provider_a_country']}"
    )


with provider_b_col:
    st.write("#### Provider B")

    st.write(
        f"**Record ID:** "
        f"{selected_match['provider_b_id']}"
    )

    st.write(
        f"**Company:** "
        f"{selected_match['provider_b_company']}"
    )

    st.write(
        f"**Address:** "
        f"{selected_match['provider_b_address']}"
    )

    st.write(
        f"**Country:** "
        f"{selected_match['provider_b_country']}"
    )


# -------------------------------------------------
# WHY THIS MATCHED
# -------------------------------------------------

st.write("### Why this matched")

left_signal, right_signal = st.columns(2)

with left_signal:
    street_score = selected_match[
        "street_similarity"
    ]

    company_score = selected_match[
        "company_similarity"
    ]

    if pd.notna(street_score):
        st.write(
            f"**Street similarity:** "
            f"{street_score * 100:.0f}%"
        )

        st.progress(
            float(street_score)
        )

    if pd.notna(company_score):
        st.write(
            f"**Company similarity:** "
            f"{company_score * 100:.0f}%"
        )

        st.progress(
            float(company_score)
        )


with right_signal:
    if selected_match["country_match"]:
        st.success(
            "Country: Exact match"
        )
    else:
        st.error(
            "Country: Conflict"
        )

    if selected_match["city_match"]:
        st.success(
            "City: Match"
        )
    else:
        st.warning(
            "City: Different or uncertain"
        )

    st.info(
        "Postal code comparison is unavailable "
        "because the source feeds do not contain "
        "postal codes."
    )


# -------------------------------------------------
# DECISION SUMMARY
# -------------------------------------------------

st.write("### Decision Summary")

reasons = []

if (
    pd.notna(
        selected_match["street_similarity"]
    )
    and selected_match[
        "street_similarity"
    ] >= 0.90
):
    reasons.append(
        "Street addresses are highly similar."
    )

if (
    pd.notna(
        selected_match["company_similarity"]
    )
    and selected_match[
        "company_similarity"
    ] >= 0.90
):
    reasons.append(
        "Company names are highly similar."
    )

if selected_match["country_match"]:
    reasons.append(
        "Country values match."
    )

if selected_match["city_match"]:
    reasons.append(
        "City values match."
    )

for reason in reasons:
    st.write(
        f"✓ {reason}"
    )


if selected_match["status"] == "exact_baseline":
    st.success(
        "This pair was identified as an exact "
        "baseline match."
    )

elif selected_match["status"] == "proposed_match":
    st.success(
        "The matching model classified these "
        "records as belonging to the same entity."
    )


# -------------------------------------------------
# MATCH METADATA
# -------------------------------------------------

with st.expander("Match metadata"):
    st.write(
        f"**Resolution run:** "
        f"{selected_match['resolution_run_id']}"
    )

    st.write(
        f"**Match rank:** "
        f"{selected_match['match_rank']}"
    )

    st.write(
        f"**Provider A record hash:** "
        f"{selected_match['provider_a_record_id']}"
    )

    st.write(
        f"**Provider B record hash:** "
        f"{selected_match['provider_b_record_id']}"
    )