import streamlit as st

PLACEHOLDER = "[description]"

SECTIONS = [
    {"id": "problem", "title": "The Problem", "body": PLACEHOLDER},
    {"id": "why", "title": "Why It Matters", "body": PLACEHOLDER},
    {"id": "approach", "title": "Our Approach", "body": PLACEHOLDER},
]

CONCEPTS = [
    {"name": "[concept or tool]", "body": PLACEHOLDER},
    {"name": "[concept or tool]", "body": PLACEHOLDER},
    {"name": "[concept or tool]", "body": PLACEHOLDER},
    {"name": "[concept or tool]", "body": PLACEHOLDER},
]

STYLE = """
<style>
/* This page only: pull content toward the sidebar. */
[data-testid="stMainBlockContainer"] {
    padding-left: 4.5rem;
    padding-right: 4.5rem;
}
.deck {
    --ink: #31333F;
    --muted: rgba(49, 51, 63, 0.62);
    --line: rgba(49, 51, 63, 0.12);
    --accent: #2563EB;
    --accent-soft: rgba(37, 99, 235, 0.08);
    max-width: 1120px;
    margin: 0;
    color: var(--ink);
}
.deck-hero {
    padding: 2.5rem 0 3.5rem;
    border-bottom: 1px solid var(--line);
}
.deck-eyebrow {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1rem;
}
.deck-hero h1 {
    font-size: clamp(2.4rem, 5vw, 3.6rem);
    line-height: 1.05;
    letter-spacing: -0.03em;
    font-weight: 800;
    margin: 0 0 1.25rem;
    padding: 0;
}
.deck-hero p {
    font-size: 1.2rem;
    line-height: 1.6;
    color: var(--muted);
    max-width: 40rem;
    margin: 0;
}
.deck-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 2rem;
}
.deck-nav a {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--ink) !important;
    text-decoration: none !important;
    padding: 0.45rem 0.9rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    transition: border-color 150ms ease, background 150ms ease;
}
.deck-nav a:hover {
    border-color: var(--accent);
    background: var(--accent-soft);
}
.deck-section {
    display: grid;
    grid-template-columns: 3.5rem 1fr;
    gap: 1.5rem;
    padding: 4rem 0;
    border-bottom: 1px solid var(--line);
    scroll-margin-top: 4rem;
}
.deck-section:last-child {
    border-bottom: none;
}
.deck-num {
    font-size: 1rem;
    font-weight: 700;
    color: var(--accent);
    font-variant-numeric: tabular-nums;
    padding-top: 0.6rem;
}
.deck-section h2 {
    font-size: clamp(1.8rem, 3.5vw, 2.5rem);
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-weight: 750;
    margin: 0 0 1rem;
    padding: 0;
}
.deck-section p {
    font-size: 1.15rem;
    line-height: 1.7;
    color: var(--muted);
    margin: 0;
    max-width: 44rem;
}
.deck-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 1.75rem;
}
.deck-card {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1.25rem 1.35rem;
    background: #fff;
}
.deck-card h3 {
    font-size: 1.05rem;
    font-weight: 650;
    margin: 0 0 0.5rem;
    padding: 0;
}
.deck-card p {
    font-size: 0.98rem;
    line-height: 1.6;
}
@media (max-width: 640px) {
    .deck-section {
        grid-template-columns: 1fr;
        gap: 0.25rem;
        padding: 2.75rem 0;
    }
    .deck-num {
        padding-top: 0;
    }
    .deck-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def section_html(number: int, section_id: str, title: str, inner: str) -> str:
    return (
        f'<section class="deck-section" id="{section_id}">'
        f'<div class="deck-num">{number:02d}</div>'
        f"<div><h2>{title}</h2>{inner}</div>"
        "</section>"
    )


nav = (
    "".join(f'<a href="#{s["id"]}">{s["title"]}</a>' for s in SECTIONS)
    + '<a href="#concepts">Concepts and Tools We Used</a>'
)

sections = "".join(
    section_html(i, s["id"], s["title"], f"<p>{s['body']}</p>")
    for i, s in enumerate(SECTIONS, start=1)
)

cards = "".join(
    f'<div class="deck-card"><h3>{c["name"]}</h3><p>{c["body"]}</p></div>'
    for c in CONCEPTS
)
sections += section_html(
    len(SECTIONS) + 1,
    "concepts",
    "Concepts and Tools We Used",
    f'<p>{PLACEHOLDER}</p><div class="deck-grid">{cards}</div>',
)

st.html(
    STYLE
    + '<div class="deck">'
    + '<header class="deck-hero">'
    + '<div class="deck-eyebrow">Altana X Databricks</div>'
    + "<h1>Address Resolution</h1>"
    + f"<p>{PLACEHOLDER}</p>"
    + f'<nav class="deck-nav">{nav}</nav>'
    + "</header>"
    + sections
    + "</div>"
)
