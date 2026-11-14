import json
import logging
import os
import re
import uuid

import pandas as pd
import streamlit as st

from data import load_gold, load_merge

ROW_HEIGHT = 35
MAX_VISIBLE_ROWS = 9
SELECTED_ROW_STYLE = "background-color: #DBEAFE"

STEP_LABELS = {
    "exact_normalized_company_address": "Exact match after cleaning",
    "fellegi_sunter_blocked": "Fellegi-Sunter model",
    "fellegi_sunter_hnsw": "Fellegi-Sunter model (vector search candidate)",
    "original_text_agreement": "Original text agreed",
    "same_company_address_settled": "Same company, same address",
    "incomplete_filled_from_resolved": "Missing field filled from a match",
}

AUTHORITY_LABELS = {
    "exact_rule": "Exact rule",
    "model_proposal_policy": "Matching model",
    "same_company_address_policy": "Same-company review",
    "incomplete_fill_policy": "Missing-field fill",
    "none": "Not merged",
}


def percent(value, digits: int = 0) -> str:
    value = pd.to_numeric(value, errors="coerce")
    return f"{value * 100:.{digits}f}%" if pd.notna(value) else "—"


def escape_markdown(text) -> str:
    """Show source-feed text literally inside Markdown-rendered elements."""
    # Collapse line breaks first so no block-level Markdown (headings, lists,
    # setext underlines) can form, then escape inline syntax.
    flat = re.sub(r"\s+", " ", str(text))
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~:$&=])", r"\\\1", flat)


def cell(value) -> str:
    """Table cell shown as literal text (st.table renders Markdown in cells)."""
    if value is None or value == "" or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return escape_markdown(value)


def source_label(provider, provider_id) -> str:
    return f"{provider}-{provider_id}"


def show_load_error(message: str, error: Exception) -> None:
    """Log the full error on the server; show users only a reference ID.
    Set APP_DEBUG=1 to also show the traceback in the page."""
    ref = uuid.uuid4().hex[:8]
    logging.getLogger(__name__).error("%s (ref=%s)", message, ref, exc_info=error)
    st.error(f"{message} Reference: `{ref}`")
    if os.getenv("APP_DEBUG") == "1":
        st.exception(error)


def json_list(value) -> list:
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

try:
    with st.spinner("Loading Gold data…"):
        gold = load_gold()
except Exception as error:  # noqa: BLE001 - surface any load failure in the UI
    show_load_error("Unable to load the Gold table.", error)
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
        placeholder="Company or address",
        icon=":material/search:",
    ).strip()

    country_options = sorted(gold["country"].dropna().unique().tolist())
    country_filter = st.multiselect(
        "Country",
        options=country_options,
        placeholder="All countries",
    )

    if st.button(
        "Refresh data",
        icon=":material/refresh:",
        help="Data is cached for an hour. Reload it from the tables now.",
        width="stretch",
    ):
        load_gold.clear()
        load_merge.clear()
        st.rerun()


# -------------------------------------------------
# FILTER DATA
# -------------------------------------------------

filtered = gold
if country_filter:
    filtered = filtered[filtered["country"].isin(country_filter)]

if search:
    needle = search.lower()
    text = (
        filtered["company"].fillna("")
        + " "
        + filtered["street_address"].fillna("")
        + " "
        + filtered["city"].fillna("")
    ).str.lower()
    filtered = filtered[text.str.contains(needle, regex=False)]

filtered = filtered.reset_index(drop=True)


# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.title("Entity Explorer")

# Center everything on this page. Data grid cells use column alignment.
st.markdown(
    """
    <style>
    [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stTable"] th,
    [data-testid="stMain"] [data-testid="stTable"] td {
        text-align: center !important;
        justify-content: center;
    }
    [data-testid="stMain"] [data-testid="stMetric"] > div,
    [data-testid="stMain"] [data-testid="stMetricLabel"],
    [data-testid="stMain"] [data-testid="stMetricValue"] {
        justify-content: center;
        justify-items: center;
        text-align: center;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

metric_1, metric_2 = st.columns(2)
metric_1.metric("Gold addresses", f"{len(filtered):,}", border=True)
metric_2.metric("Countries", f"{filtered['country'].nunique():,}", border=True)


# -------------------------------------------------
# GOLD TABLE
# -------------------------------------------------

st.subheader("Gold table")

if filtered.empty:
    st.warning("No addresses match the selected filters.")
    st.stop()

display = pd.DataFrame(
    {
        "Company": filtered["company"],
        "Street address": filtered["street_address"],
        "City": filtered["city"],
        "State": filtered["state"],
        "Country": filtered["country"],
        "Source": [
            source_label(p, i)
            for p, i in zip(filtered["provider"], filtered["provider_id"], strict=True)
        ],
    }
)

# The click from the previous run picks the row to highlight on this run.
# Cell selection has no checkbox column; any clicked cell picks its row.
previous = st.session_state.get("gold_table")
previous_cells = previous.selection.cells if previous else []
selected_index = (
    previous_cells[0][0]
    if previous_cells and previous_cells[0][0] < len(filtered)
    else None
)

styled = display.style
if selected_index is not None:
    styled = styled.map(
        lambda _: SELECTED_ROW_STYLE,
        subset=pd.IndexSlice[[selected_index], :],
    )

event = st.dataframe(
    styled,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-cell",
    key="gold_table",
    # Header row + data rows + 3px border, capped at MAX_VISIBLE_ROWS.
    height=ROW_HEIGHT * (min(len(display), MAX_VISIBLE_ROWS) + 1) + 3,
    width="stretch",
    column_config={
        "Company": st.column_config.TextColumn(alignment="center", width=190),
        "Street address": st.column_config.TextColumn(alignment="center", width=200),
        "City": st.column_config.TextColumn(alignment="center", width=110),
        "State": st.column_config.TextColumn(alignment="center", width=105),
        "Country": st.column_config.TextColumn(alignment="center", width=60),
        "Source": st.column_config.TextColumn(
            alignment="center",
            width=70,
            help="Provider and record ID of the canonical source record.",
        ),
    },
)

selected_cells = event.selection.cells
if not selected_cells or selected_cells[0][0] >= len(filtered):
    st.caption("Click a row to see its merged records.")
    st.stop()

selected_cell = selected_cells[0]
if selected_cell[0] != selected_index:
    # Rerun once so the new row is highlighted before the details load.
    st.rerun()

selected = filtered.iloc[selected_cell[0]]

# Scroll to the details only when the user clicks a new cell, not on
# every rerun (filters, refresh, etc.).
should_scroll = st.session_state.get("last_scrolled_cell") != selected_cell
st.session_state["last_scrolled_cell"] = selected_cell


# -------------------------------------------------
# MERGED RECORDS (SILVER)
# -------------------------------------------------

st.divider()
st.subheader(escape_markdown(selected["company"]), anchor="merge-details")

try:
    with st.spinner("Loading merged records from Silver…"):
        merge = load_merge(selected["provider"], selected["provider_id"])
except Exception as error:  # noqa: BLE001 - surface any load failure in the UI
    show_load_error("Unable to load the merged records.", error)
    st.stop()

if merge.empty:
    st.warning("No Silver records found for this address.")
    st.stop()

canonical = merge.iloc[0]
# Escaped once here: labels go into Markdown below.
labels = {
    row["record_id"]: escape_markdown(source_label(row["provider"], row["provider_id"]))
    for _, row in merge.iterrows()
}

authority = AUTHORITY_LABELS.get(canonical["merge_authority"], "Other")
st.markdown(
    f":blue-badge[{len(merge)} source "
    f"{'record' if len(merge) == 1 else 'records'}] "
    f":gray-badge[Merged by: {authority}] "
    f":gray[Entity ID] {escape_markdown(canonical['entity_id'])}"
)

st.markdown("#### Source records")
st.table(
    pd.DataFrame(
        {
            "Role": [
                "Kept (Gold)" if row["is_canonical"] else "Merged in"
                for _, row in merge.iterrows()
            ],
            # Non-breaking hyphen keeps "A-123" on one line.
            "Source": [labels[r].replace("\\-", "\u2011") for r in merge["record_id"]],
            "Company": merge["company"].map(cell),
            "Street address": merge["street_address"].map(cell),
            "City": merge["city"].map(cell),
            "State": merge["state"].map(cell),
            "Country": merge["country"].map(cell),
        }
    ).set_index("Role")
)


# -------------------------------------------------
# WHY THEY WERE MERGED
# -------------------------------------------------

st.markdown("#### Why they were merged")

if len(merge) == 1:
    st.info(
        "No other source record matched this one, so it went to Gold on its own.",
        icon=":material/info:",
    )
    for reason in json_list(canonical["reasons_json"]):
        st.caption(escape_markdown(reason))

# Each pair is stored on both records. Keep one copy of each.
pairs = {}
for _, row in merge.iterrows():
    for evidence in json_list(row["evidence_json"]):
        if not isinstance(evidence, dict):
            continue
        other = evidence.get("other_record_id")
        key = frozenset((row["record_id"], other))
        if other and key not in pairs:
            pairs[key] = (row["record_id"], other, evidence)

for record_id, other_id, evidence in pairs.values():
    with st.container(border=True):
        step = evidence.get("step")
        st.markdown(
            f"**{labels.get(record_id, 'Record')} ↔ "
            f"{labels.get(other_id, 'another record')}** · "
            f":gray[{STEP_LABELS.get(step) or escape_markdown(step or 'Merge')}]"
        )
        if evidence.get("reason"):
            st.markdown(escape_markdown(evidence["reason"]))

        scores = [
            ("Match probability", evidence.get("fs_match_probability")),
            ("Company similarity", evidence.get("company_jaro_winkler_similarity")),
            ("Street similarity", evidence.get("street_name_jaro_winkler_similarity")),
            ("City similarity", evidence.get("city_jaro_winkler_similarity")),
            ("Embedding similarity", evidence.get("record_cosine")),
        ]
        scores = [
            (label, value)
            for label, value in scores
            if pd.notna(pd.to_numeric(value, errors="coerce"))
        ]
        if scores:
            columns = st.columns(len(scores))
            for column, (label, value) in zip(columns, scores, strict=True):
                column.metric(label, percent(value, 1))

        if evidence.get("blocking_passes"):
            passes = str(evidence["blocking_passes"]).replace(",", ", ")
            st.caption(f"Found by blocking passes: {escape_markdown(passes)}")

filled = merge[merge["filled_field"].fillna("") != ""]
for _, row in filled.iterrows():
    field = escape_markdown(str(row["filled_field"]).replace("_", " "))
    donor = labels.get(row["filled_from_record_id"], "a matching record")
    st.info(
        f"The {field} of {labels[row['record_id']]} was missing, so it was "
        f"filled from {donor}.",
        icon=":material/edit_note:",
    )

with st.expander("Merge metadata"):
    st.table(
        pd.DataFrame(
            {
                "Value": [
                    cell(canonical["entity_id"]),
                    cell(canonical["resolved_at"]),
                    cell(
                        ", ".join(
                            STEP_LABELS.get(s, s)
                            for s in json_list(canonical["steps_json"])
                        )
                    ),
                ]
            },
            index=["Entity ID", "Resolved at", "Merge steps"],
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
            document.getElementById("merge-details")
                ?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }}, 50);
        </script>
        """,
        unsafe_allow_javascript=True,
    )
