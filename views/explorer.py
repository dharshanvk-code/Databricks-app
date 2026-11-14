import logging
import os
import re
import uuid

import pandas as pd
import streamlit as st

from data import (
    STATUS_LABELS,
    load_entities,
    load_entity_details,
    short_id,
    status_label,
)

ROW_HEIGHT = 35
MAX_VISIBLE_ROWS = 12


def percent(value, digits: int = 0) -> str:
    return f"{value * 100:.{digits}f}%" if pd.notna(value) else "—"


def escape_markdown(text) -> str:
    """Show source-feed text literally inside Markdown-rendered elements."""
    # Collapse line breaks first so no block-level Markdown (headings, lists,
    # setext underlines) can form, then escape inline syntax.
    flat = re.sub(r"\s+", " ", str(text))
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~:$&=])", r"\\\1", flat)


def cell(value) -> str:
    """Table cell shown as literal text (st.table renders Markdown in cells)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return escape_markdown(value)


def show_load_error(message: str, error: Exception) -> None:
    """Log the full error on the server; show users only a reference ID.
    Set APP_DEBUG=1 to also show the traceback in the page."""
    ref = uuid.uuid4().hex[:8]
    logging.getLogger(__name__).error("%s (ref=%s)", message, ref, exc_info=error)
    st.error(f"{message} Reference: `{ref}`")
    if os.getenv("APP_DEBUG") == "1":
        st.exception(error)


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

try:
    with st.spinner("Loading Gold data…"):
        df = load_entities()
except Exception as error:  # noqa: BLE001 - surface any load failure in the UI
    show_load_error("Unable to load Gold entity data.", error)
    st.info(
        "If you are running locally, Databricks authentication must also be "
        "configured on your machine. The deployed Databricks App "
        "authenticates automatically."
    )
    st.stop()


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.subheader("Filters")

    search = st.text_input(
        "Search",
        placeholder="Company, address or entity ID",
        icon=":material/search:",
    ).strip()

    status_options = sorted(df["status"].dropna().unique().tolist())
    status_filter = st.multiselect(
        "Status",
        options=status_options,
        default=status_options,
        format_func=status_label,
    )

    country_options = sorted(df["country"].dropna().unique().tolist())
    country_filter = st.multiselect(
        "Country",
        options=country_options,
        placeholder="All countries",
    )

    if st.button(
        "Refresh data",
        icon=":material/refresh:",
        help="Data is cached for an hour. Reload it from the Gold tables now.",
        width="stretch",
    ):
        load_entities.clear()
        load_entity_details.clear()
        st.rerun()


# -------------------------------------------------
# FILTER DATA
# -------------------------------------------------

filtered_df = df[df["status"].isin(status_filter)]

if country_filter:
    filtered_df = filtered_df[filtered_df["country"].isin(country_filter)]

if search:
    needle = search.lower()
    filtered_df = filtered_df[
        filtered_df["company"].str.lower().str.contains(needle, regex=False, na=False)
        | filtered_df["canonical_address"]
        .str.lower()
        .str.contains(needle, regex=False, na=False)
        | filtered_df["entity_id"].str.lower().str.startswith(needle, na=False)
    ]

filtered_df = filtered_df.reset_index(drop=True)


# -------------------------------------------------
# HEADER + SUMMARY METRICS
# -------------------------------------------------

st.title("Address/Entity Resolution")
st.caption(
    "Explore resolved entities, review matches, and understand why records "
    "were deduplicated."
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric("Entities", f"{len(filtered_df):,}", border=True)
metric_2.metric(
    "Exact matches",
    f"{(filtered_df['status'] == 'exact_baseline').sum():,}",
    border=True,
)
metric_3.metric(
    "Proposed matches",
    f"{(filtered_df['status'] == 'proposed_match').sum():,}",
    border=True,
)
metric_4.metric(
    "Avg. match score",
    percent(filtered_df["match_score"].mean(), 2) if len(filtered_df) else "—",
    border=True,
)


# -------------------------------------------------
# ENTITY TABLE
# -------------------------------------------------

st.subheader("Resolved Entities (Gold Table)")
st.caption("Click a row to see why its records were matched.")

if filtered_df.empty:
    st.warning("No entities match the selected filters.")
    st.stop()

display_df = pd.DataFrame(
    {
        "ID": filtered_df["entity_id"].map(short_id),
        "Company": filtered_df["company"],
        "Canonical address": filtered_df["canonical_address"],
        "Country": filtered_df["country"],
        "Match score": filtered_df["match_score"] * 100,
        "Status": filtered_df["status"].map(status_label),
    }
)

event = st.dataframe(
    display_df,
    hide_index=True,
    on_select="rerun",
    # Cell selection has no checkbox column; any clicked cell picks its row.
    selection_mode="single-cell",
    key="entity_table",
    # Header row + data rows + 3px border, capped at MAX_VISIBLE_ROWS.
    height=ROW_HEIGHT * (min(len(display_df), MAX_VISIBLE_ROWS) + 1) + 3,
    width="stretch",
    column_config={
        "ID": st.column_config.TextColumn(
            width=90,
            help="First characters of the entity hash. "
            "The full ID is shown in the details below.",
        ),
        "Company": st.column_config.TextColumn(width=220),
        "Canonical address": st.column_config.TextColumn(width=310),
        "Country": st.column_config.TextColumn(width=72),
        "Match score": st.column_config.ProgressColumn(
            width=120,
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "Status": st.column_config.TextColumn(width=120),
    },
)

selected_cells = event.selection.cells
selected_cell = selected_cells[0] if selected_cells else None
selected_index = (
    selected_cell[0] if selected_cell and selected_cell[0] < len(filtered_df) else 0
)
selected_entity = filtered_df.iloc[selected_index]["entity_id"]

# Scroll to the details only when the user clicks a new cell, not on
# every rerun (filters, pair picker, etc.).
should_scroll = (
    selected_cell is not None
    and st.session_state.get("last_scrolled_cell") != selected_cell
)
st.session_state["last_scrolled_cell"] = selected_cell


# -------------------------------------------------
# DETAIL QUERY
# -------------------------------------------------

try:
    detail_df = load_entity_details(selected_entity)
except Exception as error:  # noqa: BLE001 - surface any load failure in the UI
    show_load_error("Unable to load entity match details.", error)
    st.stop()

if detail_df.empty:
    st.warning("No match details found for this entity.")
    st.stop()


# -------------------------------------------------
# MATCH EXPLANATION
# -------------------------------------------------

best_match = detail_df.iloc[0]

st.divider()

st.subheader(escape_markdown(best_match["company"]), anchor="entity-details")

decision = best_match["status"]
badge_color = "green" if decision == "exact_baseline" else "blue"
st.markdown(
    f":{badge_color}-badge[{STATUS_LABELS.get(decision, 'Other')}] "
    f":gray[Entity ID] `{selected_entity}`"
)

score_col, pairs_col, country_col = st.columns(3)
score_col.metric(
    "Overall match score", percent(best_match["match_score"], 2), border=True
)
pairs_col.metric("Matched pairs", f"{len(detail_df):,}", border=True)
country_col.metric("Country", best_match["country"], border=True)


# -------------------------------------------------
# PICK A MATCHED PAIR
# -------------------------------------------------

if len(detail_df) > 1:
    match_options = [
        f"Pair {int(row['match_rank'])}: A-{row['provider_a_id']} ↔ "
        f"B-{row['provider_b_id']} ({percent(row['match_score'], 1)})"
        for _, row in detail_df.iterrows()
    ]

    selected_match_label = st.selectbox(
        f"This entity has {len(detail_df)} Provider A ↔ Provider B pairs",
        match_options,
    )
    selected_match = detail_df.iloc[match_options.index(selected_match_label)]
else:
    selected_match = best_match


# -------------------------------------------------
# SOURCE RECORDS
# -------------------------------------------------

st.markdown("#### Source records")

rows = [
    ("Record ID", "provider_a_id", "provider_b_id"),
    ("Company", "provider_a_company", "provider_b_company"),
    ("Address", "provider_a_address", "provider_b_address"),
    ("Country", "provider_a_country", "provider_b_country"),
]
st.table(
    pd.DataFrame(
        {
            "Provider A": [cell(selected_match[a]) for _, a, _ in rows],
            "Provider B": [cell(selected_match[b]) for _, _, b in rows],
        },
        index=[label for label, _, _ in rows],
    )
)


# -------------------------------------------------
# WHY THIS MATCHED
# -------------------------------------------------

st.markdown("#### Why this matched")

similarity_col, checks_col = st.columns(2)

with similarity_col, st.container(border=True, height="stretch"):
    for label, column in [
        ("Street similarity", "street_similarity"),
        ("Company similarity", "company_similarity"),
    ]:
        score = selected_match[column]
        if pd.notna(score):
            st.progress(float(score), text=f"{label} · {percent(score)}")
        else:
            st.caption(f"{label}: not available")

with checks_col, st.container(border=True, height="stretch"):
    if selected_match["country_match"]:
        st.markdown(":green[:material/check_circle:] Country matches exactly")
    else:
        st.markdown(":red[:material/cancel:] Country conflict")

    if selected_match["city_match"]:
        st.markdown(":green[:material/check_circle:] City matches")
    else:
        st.markdown(":orange[:material/help:] City differs or is uncertain")

    st.markdown(
        ":gray[:material/remove_circle_outline:] :gray[Postal code not compared. "
        "The source feeds have no postal codes.]"
    )

reasons = []
if (
    pd.notna(selected_match["street_similarity"])
    and selected_match["street_similarity"] >= 0.90
):
    reasons.append("street addresses are highly similar")
if (
    pd.notna(selected_match["company_similarity"])
    and selected_match["company_similarity"] >= 0.90
):
    reasons.append("company names are highly similar")
if selected_match["country_match"]:
    reasons.append("countries match")
if selected_match["city_match"]:
    reasons.append("cities match")

reason_text = f" Evidence: {', '.join(reasons)}." if reasons else ""

if selected_match["status"] == "exact_baseline":
    st.success(
        "Identified as an exact baseline match." + reason_text,
        icon=":material/verified:",
    )
elif selected_match["status"] == "proposed_match":
    st.info(
        "The matching model classified these records as the same entity." + reason_text,
        icon=":material/link:",
    )


# -------------------------------------------------
# MATCH METADATA
# -------------------------------------------------

with st.expander("Match metadata"):
    metadata = [
        ("Resolution run", selected_match["resolution_run_id"]),
        ("Resolved at", selected_match["resolved_at"]),
        ("Match rank", selected_match["match_rank"]),
        ("Match weight", selected_match["match_weight"]),
        (
            "Company Levenshtein",
            percent(selected_match["company_levenshtein_similarity"], 1),
        ),
        (
            "Street Jaro-Winkler",
            percent(selected_match["street_jaro_winkler_similarity"], 1),
        ),
        (
            "City Jaro-Winkler",
            percent(selected_match["city_jaro_winkler_similarity"], 1),
        ),
        ("Provider A record hash", selected_match["provider_a_record_id"]),
        ("Provider B record hash", selected_match["provider_b_record_id"]),
    ]
    st.table(
        pd.DataFrame(
            {"Value": [cell(value) for _, value in metadata]},
            index=[label for label, _ in metadata],
        )
    )


# -------------------------------------------------
# SCROLL TO DETAILS AFTER A ROW CLICK
# -------------------------------------------------

if should_scroll:
    st.session_state["scroll_nonce"] = st.session_state.get("scroll_nonce", 0) + 1
    # The nonce makes the HTML differ each time so the script runs again.
    st.html(
        f"""
        <script data-nonce="{st.session_state["scroll_nonce"]}">
        setTimeout(() => {{
            document.getElementById("entity-details")
                ?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }}, 50);
        </script>
        """,
        unsafe_allow_javascript=True,
    )
