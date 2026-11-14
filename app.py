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

    /*
     * Agent chat in the sidebar (genie_chat.py). The sidebar is narrow, so
     * drop the avatars and mark questions with a white bubble instead.
     */
    [data-testid="stSidebar"] [data-testid="stChatMessage"] {
        padding: 0;
        gap: 0;
        background: transparent;
    }
    [data-testid="stSidebar"] [data-testid^="stChatMessageAvatar"] {
        display: none;
    }
    [data-testid="stSidebar"] [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarUser"]
    ) {
        box-sizing: border-box;
        width: calc(100% - 1.5rem);
        margin-left: 1.5rem;
        padding: 0.6rem 0.85rem;
        border-radius: 0.75rem;
        background: #FFFFFF;
    }
    .genie-progress {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        color: rgba(49, 51, 63, 0.6);
        font-size: 0.875rem;
    }
    .genie-progress::before {
        content: "";
        flex: none;
        width: 0.9rem;
        height: 0.9rem;
        border: 2px solid rgba(37, 99, 235, 0.25);
        border-top-color: #2563EB;
        border-radius: 50%;
        animation: genie-spin 0.8s linear infinite;
    }
    @keyframes genie-spin {
        to { transform: rotate(360deg); }
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

    /*
     * Detail tables (st.table): Streamlit caps cell text at 400px on one line,
     * which cuts off long addresses and hashes. Let cells use the full column
     * and wrap, and keep the row-label column narrow.
     */
    [data-testid="stTable"] td,
    [data-testid="stTable"] th {
        white-space: normal;
    }
    [data-testid="stTable"] td [data-testid="stMarkdownContainer"] {
        max-width: none;
        overflow-wrap: anywhere;
    }
    [data-testid="stTable"] tbody th {
        width: 11rem;
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
