import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Altana Entity Resolution",
    layout="wide"
)

st.title("Altana Entity Resolution")
st.caption("Explore resolved entities and deduplication decisions.")

df = pd.read_csv("mock_gold.csv")

with st.sidebar:
    st.header("Entity Resolution Agent")

    question = st.text_input(
        "Ask about the data",
        placeholder="Why was E001 matched?"
    )

    if question:
        st.info("Agent functionality coming soon.")

    st.divider()

    status_filter = st.multiselect(
        "Status",
        options=df["status"].unique(),
        default=df["status"].unique()
    )

filtered_df = df[df["status"].isin(status_filter)]

st.subheader("Resolved Entities")

st.dataframe(
    filtered_df[
        [
            "entity_id",
            "company",
            "canonical_address",
            "country",
            "match_score",
            "status"
        ]
    ],
    hide_index=True
)

st.divider()

st.subheader("Match Explanation")

entity_options = filtered_df["entity_id"].tolist()

if entity_options:
    selected_entity = st.selectbox(
        "Select an entity",
        entity_options
    )

    row = filtered_df[
        filtered_df["entity_id"] == selected_entity
    ].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Overall Match Score",
            f"{row['match_score'] * 100:.0f}%"
        )

        st.write(f"**Company:** {row['company']}")
        st.write(f"**Address:** {row['canonical_address']}")
        st.write(f"**Country:** {row['country']}")
        st.write(f"**Status:** {row['status']}")

    with col2:
        st.write("### Matching Signals")

        st.write(
            f"Street similarity: "
            f"{row['street_similarity'] * 100:.0f}%"
        )

        st.write(
            f"Company similarity: "
            f"{row['company_similarity'] * 100:.0f}%"
        )

        st.write(
            f"City match: "
            f"{'Yes' if row['city_match'] else 'No'}"
        )

        st.write(
            f"Postal match: "
            f"{'Yes' if row['postal_match'] else 'No'}"
        )

        st.write(
            f"Country match: "
            f"{'Yes' if row['country_match'] else 'No'}"
        )

else:
    st.warning("No entities match the selected filters.")