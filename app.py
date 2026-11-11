import contextlib

import streamlit as st

from data import load_entities

st.set_page_config(
    page_title="Altana x Databricks",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* App name in the sidebar header, beside the collapse button. */
    [data-testid="stSidebarHeader"] {
        align-items: center;
    }
    [data-testid="stSidebarHeader"]::before {
        content: "Altana X Databricks";
        flex: 1 1 auto;
        min-width: 0;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #31333F;
    }

    /* Keep the sidebar collapse control visible, not only on hover. */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
    }

    /*
     * Smooth sidebar open/close. Streamlit animates max-width (600px -> 0)
     * while the sidebar is only ~300px wide, so the width sits still for the
     * first half and then snaps. Animate the real width instead, with one
     * shared easing curve for every property.
     */
    [data-testid="stSidebar"] {
        max-width: 600px !important;
        transition:
            transform 320ms cubic-bezier(0.4, 0, 0.2, 1),
            width 320ms cubic-bezier(0.4, 0, 0.2, 1),
            min-width 320ms cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
    }
    /* No easing while the user drags the sidebar edge to resize it. */
    [data-testid="stSidebar"][style*="user-select: none"] {
        transition: none !important;
    }

    /* Tighter top spacing for the main column. */
    [data-testid="stMainBlockContainer"] {
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    /* Smaller metric values so long names fit in one line. */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
    }

    /* Comparison table: fill the card and wrap long addresses. */
    [data-testid="stMarkdownContainer"] table {
        width: 100%;
    }
    [data-testid="stMarkdownContainer"] th:first-child,
    [data-testid="stMarkdownContainer"] td:first-child {
        width: 7.5rem;
        color: rgba(49, 51, 63, 0.6);
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

navigation = st.navigation(
    [
        st.Page(
            "views/presentation.py",
            title="Presentation",
            icon=":material/slideshow:",
            url_path="presentation",
        ),
        st.Page(
            "views/explorer.py",
            title="Entity Explorer",
            icon=":material/table_view:",
            default=True,
        ),
    ]
)

navigation.run()

# Warm the Gold-table cache after the current page has rendered, so opening
# the Entity Explorer from another page is instant.
# The explorer page reports load errors itself, so ignore them here.
with contextlib.suppress(Exception):
    load_entities()
