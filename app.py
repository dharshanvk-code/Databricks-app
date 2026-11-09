import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Altana Entity Resolution",
    layout="wide"
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

df = pd.read_csv("mock_gold.csv")

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.title("Altana Entity Resolution")
st.caption(
    "Explore resolved entities, review uncertain matches, "
    "and understand why records were deduplicated."
)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.header("Entity Resolution Agent")

    question = st.text_input(
        "Ask about the data",
        placeholder="Why was E001 matched?"
    )

    if question:
        q = question.lower()

        if "review" in q:
            review_count = len(df[df["status"] == "Review"])
            st.success(f"There are {review_count} entities currently in review.")

        elif "matched" in q and "how many" in q:
            matched_count = len(df[df["status"] == "Matched"])
            st.success(f"There are {matched_count} matched entities.")

        elif "under 85" in q or "below 85" in q:
            low_confidence = df[df["match_score"] < 0.85]

            if low_confidence.empty:
                st.info("There are no entities below 85% confidence.")
            else:
                st.write("Entities below 85% confidence:")
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

        elif "why" in q:
            entity_found = None

            for entity_id in df["entity_id"]:
                if entity_id.lower() in q:
                    entity_found = entity_id
                    break

            if entity_found:
                row = df[df["entity_id"] == entity_found].iloc[0]

                st.write(f"### {entity_found}")
                st.write(
                    f"Match score: "
                    f"{row['match_score'] * 100:.0f}%"
                )
                st.write(
                    f"Street similarity: "
                    f"{row['street_similarity'] * 100:.0f}%"
                )
                st.write(
                    f"Company similarity: "
                    f"{row['company_similarity'] * 100:.0f}%"
                )
                st.write(
                    f"Country match: "
                    f"{'Yes' if row['country_match'] else 'No'}"
                )
            else:
                st.info(
                    "Include an entity ID, for example: "
                    "'Why was E001 matched?'"
                )

        else:
            st.info(
                "Try asking:\n\n"
                "- Why was E001 matched?\n"
                "- How many are matched?\n"
                "- How many are in review?\n"
                "- Show matches under 85%"
            )

    st.divider()

    status_filter = st.multiselect(
        "Status",
        options=df["status"].unique(),
        default=df["status"].unique()
    )

    country_filter = st.multiselect(
        "Country",
        options=sorted(df["country"].dropna().unique()),
        default=[]
    )

# -------------------------------------------------
# FILTER DATA
# -------------------------------------------------

filtered_df = df[df["status"].isin(status_filter)].copy()

if country_filter:
    filtered_df = filtered_df[
        filtered_df["country"].isin(country_filter)
    ]

# -------------------------------------------------
# SUMMARY METRICS
# -------------------------------------------------

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric("Entities", len(filtered_df))

with metric2:
    matched_count = len(
        filtered_df[filtered_df["status"] == "Matched"]
    )
    st.metric("Matched", matched_count)

with metric3:
    review_count = len(
        filtered_df[filtered_df["status"] == "Review"]
    )
    st.metric("Review", review_count)

with metric4:
    if len(filtered_df) > 0:
        avg_score = filtered_df["match_score"].mean() * 100
        st.metric("Avg. Match Score", f"{avg_score:.1f}%")
    else:
        st.metric("Avg. Match Score", "—")

# -------------------------------------------------
# ENTITY TABLE
# -------------------------------------------------

st.subheader("Resolved Entities")
st.caption("Select a row to inspect the deduplication decision.")

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
    display_df["match_score"] * 100
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

if not display_df.empty:

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

    selected_row = filtered_df.iloc[selected_index]

else:
    selected_row = None
    st.warning("No entities match the selected filters.")

# -------------------------------------------------
# MATCH EXPLANATION
# -------------------------------------------------

if selected_row is not None:

    st.divider()

    st.subheader(
        f"Entity {selected_row['entity_id']} — Match Explanation"
    )

    score = selected_row["match_score"]

    if selected_row["status"] == "Matched":
        decision_text = "Duplicate / Existing Entity"
    elif selected_row["status"] == "Review":
        decision_text = "Needs Review"
    else:
        decision_text = selected_row["status"]

    score_col, decision_col, company_col = st.columns(3)

    with score_col:
        st.metric(
            "Overall Match Score",
            f"{score * 100:.0f}%"
        )

    with decision_col:
        st.metric(
            "Decision",
            decision_text
        )

    with company_col:
        st.metric(
            "Canonical Company",
            selected_row["company"]
        )

    # ---------------------------------------------
    # PROVIDER COMPARISON
    # ---------------------------------------------

    st.write("### Source Records")

    provider_a_col, provider_b_col = st.columns(2)

    with provider_a_col:
        st.write("#### Provider A")

        st.write(
            f"**Record ID:** "
            f"{selected_row['provider_a_id']}"
        )

        st.write(
            f"**Company:** "
            f"{selected_row['provider_a_company']}"
        )

        st.write(
            f"**Address:** "
            f"{selected_row['provider_a_address']}"
        )

        st.write(
            f"**Country:** "
            f"{selected_row['provider_a_country']}"
        )

    with provider_b_col:
        st.write("#### Provider B")

        st.write(
            f"**Record ID:** "
            f"{selected_row['provider_b_id']}"
        )

        st.write(
            f"**Company:** "
            f"{selected_row['provider_b_company']}"
        )

        st.write(
            f"**Address:** "
            f"{selected_row['provider_b_address']}"
        )

        st.write(
            f"**Country:** "
            f"{selected_row['provider_b_country']}"
        )

    # ---------------------------------------------
    # MATCH SIGNALS
    # ---------------------------------------------

    st.write("### Why this matched")

    signal_col1, signal_col2 = st.columns(2)

    with signal_col1:

        st.write(
            f"**Street similarity:** "
            f"{selected_row['street_similarity'] * 100:.0f}%"
        )

        st.progress(
            float(selected_row["street_similarity"])
        )

        st.write(
            f"**Company similarity:** "
            f"{selected_row['company_similarity'] * 100:.0f}%"
        )

        st.progress(
            float(selected_row["company_similarity"])
        )

    with signal_col2:

        if selected_row["country_match"]:
            st.success("Country: Exact match")
        else:
            st.error("Country: Conflict")

        if selected_row["postal_match"]:
            st.success("Postal code: Exact match")
        else:
            st.warning("Postal code: Missing or different")

        if selected_row["city_match"]:
            st.success("City: Match")
        else:
            st.warning("City: Missing or different")

    # ---------------------------------------------
    # DECISION EXPLANATION
    # ---------------------------------------------

    st.write("### Decision Summary")

    reasons = []

    if selected_row["street_similarity"] >= 0.9:
        reasons.append(
            "The street addresses are highly similar."
        )

    if selected_row["company_similarity"] >= 0.9:
        reasons.append(
            "The company names are highly similar."
        )

    if selected_row["country_match"]:
        reasons.append(
            "The country values match."
        )

    if selected_row["postal_match"]:
        reasons.append(
            "The postal codes match."
        )

    if selected_row["city_match"]:
        reasons.append(
            "The city values match."
        )

    if not selected_row["country_match"]:
        st.error(
            "The countries conflict. This should normally "
            "prevent an automatic duplicate match."
        )

    else:
        for reason in reasons:
            st.write(f"✓ {reason}")

        if selected_row["status"] == "Matched":
            st.success(
                "The available evidence is strong enough "
                "to classify these records as the same entity."
            )

        elif selected_row["status"] == "Review":
            st.warning(
                "The records are similar, but the evidence "
                "is not strong enough for an automatic merge."
            )