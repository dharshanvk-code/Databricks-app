import base64
from html import escape
from pathlib import Path

import streamlit as st

PLACEHOLDER = "[description]"
ASSETS = Path(__file__).parent / "assets"

# Figures below come from the live workspace (addressresolution catalog):
# silver.address_pipeline_accounting, silver.dlq_routing_audit, and the
# scoring run 181739853920898_unified_1 that built the current Gold table.

SECTIONS = [
    {"id": "problem", "title": "The Problem", "body": PLACEHOLDER},
    {"id": "why", "title": "Why It Matters", "body": PLACEHOLDER},
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
    --faint: rgba(49, 51, 63, 0.45);
    --line: rgba(49, 51, 63, 0.12);
    --panel: #F7F8FA;
    --accent: #2563EB;
    --accent-soft: rgba(37, 99, 235, 0.08);
    --query: #EB6834;
    --good: #12805C;
    --bad: #C2410C;
    max-width: 1120px;
    margin: 0 auto;
    color: var(--ink);
    text-align: center;
}
.deck code {
    font-size: 0.8em;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 0.3rem;
    padding: 0.05rem 0.3rem;
    color: var(--ink);
    overflow-wrap: anywhere;
}
.deck-hero {
    padding: 2.5rem 0 3.5rem;
    border-bottom: 1px solid var(--line);
}
.deck-logos {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.25rem;
    margin-bottom: 1.75rem;
}
.deck-logos img {
    display: block;
    width: auto;
}
.deck-logos .logo-altana {
    height: 1.9rem;
}
.deck-logos .logo-databricks {
    height: 1.55rem;
}
.deck-logos-x {
    font-size: 1.1rem;
    color: var(--faint);
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
    max-width: 56rem;
    margin: 0 auto;
}
.deck-hero .deck-authors {
    font-size: 1rem;
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 0.75rem;
}
.deck-nav {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
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
    padding: 4rem 0;
    border-bottom: 1px solid var(--line);
    scroll-margin-top: 4rem;
}
/* Demo: an almost empty section, the cue to switch to the live app. */
.deck-demo {
    min-height: 70vh;
    display: grid;
    place-items: center;
}
.deck-section.deck-demo h2 {
    font-size: clamp(3.5rem, 9vw, 6.5rem);
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0;
}

.deck-section:last-child {
    border-bottom: none;
}
.deck-num {
    font-size: 1rem;
    font-weight: 700;
    color: var(--accent);
    font-variant-numeric: tabular-nums;
    margin-bottom: 0.5rem;
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
    margin: 0 auto;
    max-width: 60rem;
}
.deck-section p + p {
    margin-top: 0.9rem;
}
.deck-section strong {
    color: var(--ink);
    font-weight: 650;
}

/* Sub-steps inside a section. */
.deck-step {
    margin-top: 3.5rem;
    scroll-margin-top: 4rem;
}
.deck-kicker {
    font-size: 0.78rem;
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.4rem;
}
.deck-step h3,
.deck-sub h3 {
    font-size: 1.45rem;
    line-height: 1.25;
    letter-spacing: -0.01em;
    font-weight: 720;
    margin: 0 0 0.75rem;
    padding: 0;
}
.deck-step h4 {
    font-size: 1.05rem;
    font-weight: 680;
    margin: 1.75rem 0 0.6rem;
    padding: 0;
}
.deck-list {
    /* Streamlit pads lists; centered lines need none. */
    margin: 1rem auto 0 !important;
    padding: 0 !important;
    list-style: none;
    max-width: 60rem;
}
.deck-list li {
    font-size: 1.05rem;
    line-height: 1.65;
    color: var(--muted);
    margin: 0.6rem 0;
}
.deck-note {
    font-size: 0.9rem !important;
    color: var(--faint) !important;
    margin-top: 0.75rem !important;
}

/* Pipeline overview. */
.flow {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 2rem;
}
.flow-card {
    position: relative;
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1.1rem 1.15rem 1.2rem;
    background: #fff;
}
.flow-card:not(:last-child)::after {
    content: "";
    position: absolute;
    top: 50%;
    right: -0.6rem;
    width: 0.45rem;
    height: 0.45rem;
    border-top: 2px solid var(--faint);
    border-right: 2px solid var(--faint);
    transform: translateY(-50%) rotate(45deg);
}
.flow-layer {
    font-size: 0.75rem;
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
}
.flow-card h4 {
    font-size: 1.02rem;
    font-weight: 680;
    margin: 0.3rem 0 0.6rem;
    padding: 0;
}
.flow-stat {
    font-size: 1.6rem;
    font-weight: 720;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}
.flow-stat span {
    display: block;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0;
    color: var(--muted);
    margin-top: 0.15rem;
}
.flow-card p {
    font-size: 0.92rem !important;
    line-height: 1.55 !important;
    margin-top: 0.7rem !important;
}

/* Row accounting bars. */
.rows {
    margin: 2.25rem auto 0;
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1.25rem 1.35rem 1.1rem;
    background: #fff;
    max-width: 52rem;
}
.rows-title {
    font-size: 1rem;
    font-weight: 680;
    margin-bottom: 0.2rem;
}
.rows-sub {
    font-size: 0.88rem;
    color: var(--muted);
    margin-bottom: 1rem;
}
.rows-row {
    display: grid;
    grid-template-columns: minmax(0, 15rem) minmax(0, 1fr);
    gap: 0.9rem;
    align-items: center;
    padding: 0.38rem 0;
    border-radius: 0.4rem;
    /* A bar chart: labels stay aligned to their bars. */
    text-align: left;
}
.rows-row:hover {
    background: var(--panel);
}
.rows-label {
    font-size: 0.9rem;
    line-height: 1.35;
    color: var(--ink);
}
.rows-label small {
    display: block;
    font-size: 0.78rem;
    color: var(--muted);
}
.rows-track {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 0;
}
.rows-bar {
    /* --w is the share of the largest value; leave room for the label. */
    width: calc((100% - 7.5rem) * var(--w));
    height: 0.85rem;
    min-width: 3px;
    border-radius: 0 4px 4px 0;
    background: var(--accent);
    flex: 0 0 auto;
}
.rows-bar.is-held {
    background: #6D9BF1;
}
.rows-value {
    font-size: 0.88rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.rows-value span {
    font-weight: 400;
    color: var(--muted);
}

/* Small comparison table. */
.deck-table {
    width: 100%;
    max-width: 50rem;
    border-collapse: collapse;
    margin: 1.25rem auto 0;
    font-size: 0.92rem;
}
.deck-table th,
.deck-table td {
    text-align: center;
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
    line-height: 1.45;
}
.deck-table th {
    font-size: 0.76rem;
    font-weight: 650;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
}
.deck-table td {
    color: var(--ink);
}
.deck-table td.num {
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    font-weight: 600;
}
.deck-table td.dim {
    color: var(--muted);
}
.deck-table td:first-child {
    white-space: nowrap;
}
/* Space between a block (table, grid, list) and the paragraph after it. */
.stats + p,
.tiers + p,
.table-wrap + p,
.deck-list + p,
.stages + p {
    margin-top: 1.25rem !important;
}
.table-wrap {
    overflow-x: auto;
    max-width: 100%;
}

/* Translation tiers. */
.tiers {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.5rem;
    counter-reset: tier;
}
.tier {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1rem 1.05rem;
    background: #fff;
}
.tier-tag {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    margin-bottom: 0.55rem;
}
.tier-tag.is-rule {
    color: #1E3A8A;
    background: var(--accent-soft);
}
.tier-tag.is-ai {
    color: #9A3412;
    background: rgba(235, 104, 52, 0.1);
}
.tier h4 {
    font-size: 1rem;
    font-weight: 680;
    margin: 0 0 0.4rem;
    padding: 0;
}
.tier p {
    font-size: 0.9rem !important;
    line-height: 1.55 !important;
}

/* Stat strip. */
.stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.25rem;
}
.stat {
    background: var(--panel);
    border-radius: 0.75rem;
    padding: 0.9rem 1rem;
}
.stat-value {
    font-size: 1.45rem;
    font-weight: 720;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}
.stat-label {
    font-size: 0.85rem;
    line-height: 1.4;
    color: var(--muted);
    margin-top: 0.15rem;
}

/* Matching stages. */
.stages {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.5rem;
}
.stage {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1rem 1.05rem;
    background: #fff;
}
.stage-kind {
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
}
.stage h4 {
    font-size: 1rem;
    font-weight: 680;
    margin: 0.25rem 0 0.4rem;
    padding: 0;
}
.stage p {
    font-size: 0.9rem !important;
    line-height: 1.55 !important;
}

/* Scroll-driven vector search explainer. */
.vs {
    display: grid;
    grid-template-columns: minmax(0, 20rem) minmax(0, 1fr);
    gap: 2.5rem;
    margin-top: 2.5rem;
    position: relative;
}
.vs-steps {
    padding: 8vh 0 30vh;
}
.vs-step {
    min-height: 62vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: left;
    opacity: 0.32;
    transition: opacity 250ms ease;
}
.vs-step.is-active {
    opacity: 1;
}
.vs-step .deck-kicker {
    color: var(--query);
}
.vs-step h4 {
    font-size: 1.25rem;
    font-weight: 720;
    margin: 0 0 0.6rem;
    padding: 0;
    letter-spacing: -0.01em;
}
.vs-step p {
    font-size: 1rem !important;
    line-height: 1.65 !important;
}
.vs-stage {
    position: sticky;
    top: 4.5rem;
    height: calc(100vh - 6rem);
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
}
.vs-frame {
    border: 1px solid var(--line);
    border-radius: 0.9rem;
    background: #fff;
    padding: 0.75rem;
}
.vs-svg {
    display: block;
    width: 100%;
    height: auto;
    max-height: calc(100vh - 11rem);
}
.vs-svg text {
    font-family: inherit;
}
.vs-label {
    font-size: 14px;
    font-weight: 600;
    fill: #31333F;
}
.vs-sub {
    font-size: 13px;
    fill: rgba(49, 51, 63, 0.7);
}
.vs-row {
    font-size: 16px;
    fill: #31333F;
}
.vs-small {
    font-size: 13.5px;
    fill: rgba(49, 51, 63, 0.7);
}
.vs-counter {
    font-size: 16px;
    font-weight: 650;
    fill: #31333F;
}
.vs-plane-label {
    font-size: 13px;
    font-weight: 600;
    fill: rgba(49, 51, 63, 0.62);
}
.vs-narrow .vs-label { font-size: 19px; }
.vs-narrow .vs-sub { font-size: 17px; }
.vs-narrow .vs-row { font-size: 19px; }
.vs-narrow .vs-small { font-size: 18px; }
.vs-narrow .vs-counter { font-size: 19px; }
.vs-narrow .vs-plane-label { font-size: 17px; }
.vs-legend {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.4rem 1.1rem;
    margin-top: 0.6rem;
    font-size: 0.82rem;
    color: var(--muted);
}
.vs-legend span::before {
    content: "";
    display: inline-block;
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    margin-right: 0.4rem;
    vertical-align: -0.03rem;
    background: var(--c);
}
.vs-caption {
    font-size: 0.8rem;
    color: var(--faint);
    margin-top: 0.35rem;
}

/* Worked scoring examples. */
.pairs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 1.5rem;
}
.pair {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1.1rem 1.2rem 1.15rem;
    background: #fff;
    min-width: 0;
}
.pair-records {
    display: grid;
    gap: 0.4rem;
    margin-bottom: 0.9rem;
}
.pair-record {
    font-size: 0.86rem;
    line-height: 1.45;
    background: var(--panel);
    border-radius: 0.5rem;
    padding: 0.45rem 0.65rem;
    overflow-wrap: anywhere;
}
.pair-record b {
    font-weight: 650;
}
.ev {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 6.5rem 3.6rem;
    gap: 0.5rem;
    align-items: center;
    font-size: 0.86rem;
    padding: 0.28rem 0;
    border-bottom: 1px dashed var(--line);
    /* Evidence chart: names left, values right, bars on a shared zero line. */
    text-align: left;
}
.ev-name small {
    display: block;
    color: var(--muted);
    font-size: 0.76rem;
}
.ev-track {
    position: relative;
    height: 0.5rem;
}
.ev-track::before {
    content: "";
    position: absolute;
    left: 50%;
    top: -0.3rem;
    bottom: -0.3rem;
    width: 1px;
    background: rgba(49, 51, 63, 0.25);
}
.ev-bar {
    position: absolute;
    top: 0;
    height: 0.5rem;
    left: 50%;
    border-radius: 0 3px 3px 0;
    background: var(--accent);
}
.ev-bar.is-neg {
    left: auto;
    right: 50%;
    background: #A3A8B4;
    border-radius: 3px 0 0 3px;
}
.ev-val {
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
}
.ev.is-total {
    border-bottom: none;
    padding-top: 0.5rem;
    font-weight: 650;
}
.verdict {
    margin-top: 0.8rem;
    padding: 0.6rem 0.75rem;
    border-radius: 0.5rem;
    font-size: 0.88rem;
    line-height: 1.45;
}
.verdict b {
    font-weight: 700;
}
.verdict.is-good {
    background: rgba(27, 175, 122, 0.1);
    color: #0F5D43;
}
.verdict.is-bad {
    background: rgba(235, 104, 52, 0.1);
    color: #8A2E0C;
}
.rule {
    margin: 1.25rem auto 0;
    background: var(--accent-soft);
    border-radius: 0.6rem;
    padding: 0.9rem 1.25rem;
    max-width: 60rem;
}
.rule p {
    font-size: 0.98rem !important;
    color: var(--ink) !important;
}

/* Problems we ran into. */
.issues {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.5rem;
}
.issue {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1rem 1.05rem;
    background: #fff;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
}
.issue-where {
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
}
.issue h4 {
    font-size: 1rem;
    font-weight: 680;
    margin: 0;
    padding: 0;
    line-height: 1.35;
}
.issue p {
    font-size: 0.9rem !important;
    line-height: 1.55 !important;
}
.issue .fix {
    color: var(--ink) !important;
    border-top: 1px solid var(--line);
    padding-top: 0.5rem;
    margin-top: auto !important;
}
.issue .fix b {
    color: var(--good);
}

/* Concepts and tools. */
.deck-sub {
    margin-top: 2.5rem;
}
.deck-sub h3 {
    margin-bottom: 0.25rem;
}
.deck-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.1rem;
}
.deck-card {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1.05rem 1.15rem 1.1rem;
    background: #fff;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
}
.deck-card h4 {
    font-size: 1.02rem;
    font-weight: 680;
    margin: 0;
    padding: 0;
}
.deck-card p {
    font-size: 0.92rem !important;
    line-height: 1.55 !important;
}
.deck-card .used {
    font-size: 0.85rem !important;
    color: var(--ink) !important;
    border-top: 1px solid var(--line);
    padding-top: 0.5rem;
    margin-top: auto !important;
}
.deck-card .used b {
    color: var(--accent);
    font-weight: 650;
}

@media (max-width: 1100px) {
    .flow,
    .tiers,
    .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .flow-card:not(:last-child)::after {
        display: none;
    }
    .issues,
    .deck-grid,
    .stages {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .pairs {
        grid-template-columns: 1fr;
    }
}
@media (max-width: 820px) {
    .vs {
        grid-template-columns: 1fr;
        gap: 0;
    }
    .vs-stage {
        order: -1;
        top: 3.75rem;
        height: auto;
        z-index: 1;
        background: #fff;
        padding-bottom: 0.5rem;
    }
    .vs-svg {
        max-height: 46vh;
    }
    .vs-steps {
        padding: 4vh 0 20vh;
    }
    .vs-step {
        min-height: 62vh;
    }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .deck-section {
        padding: 2.75rem 0;
    }
    .deck-logos {
        gap: 0.9rem;
    }
    .deck-logos .logo-altana {
        height: 1.5rem;
    }
    .deck-logos .logo-databricks {
        height: 1.2rem;
    }
    .flow,
    .tiers,
    .stats,
    .issues,
    .deck-grid,
    .stages {
        grid-template-columns: minmax(0, 1fr);
    }
    .rows-row {
        grid-template-columns: minmax(0, 1fr);
        gap: 0.3rem;
    }
    .vs-legend {
        font-size: 0.75rem;
    }
}
@media (prefers-reduced-motion: reduce) {
    .vs-step {
        transition: none;
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


def step_html(kicker: str, title: str, inner: str, step_id: str = "") -> str:
    id_attr = f' id="{step_id}"' if step_id else ""
    return (
        f'<div class="deck-step"{id_attr}>'
        f'<div class="deck-kicker">{kicker}</div>'
        f"<h3>{title}</h3>{inner}</div>"
    )


# ---------------------------------------------------------------------------
# 03 Our Approach
# ---------------------------------------------------------------------------

FLOW = [
    (
        "Bronze",
        "Ingest",
        "35,185",
        "raw rows from 2 providers",
        "We loaded two synthetic CSV feeds into raw tables with Auto Loader.",
    ),
    (
        "Silver",
        "Clean and translate",
        "33,716",
        "rows ready to match",
        (
            "We cleaned both feeds, merged them into one schema, and translated "
            "non-Latin text. Rows that broke a rule went to a dead letter queue."
        ),
    ),
    (
        "Matching",
        "Find and score duplicates",
        "1.02M",
        "candidate pairs scored",
        (
            "We found likely duplicates with blocking and vector search, scored them "
            "with a probabilistic model, and blocked risky merges with hard rules."
        ),
    ),
    (
        "Gold",
        "Publish",
        "20,538",
        "resolved addresses",
        (
            "We kept one complete address per company and location, linked to "
            "every source record behind it."
        ),
    ),
]

flow_html = (
    '<div class="flow">'
    + "".join(
        f'<div class="flow-card"><div class="flow-layer">{layer}</div>'
        f"<h4>{title}</h4>"
        f'<div class="flow-stat">{stat}<span>{unit}</span></div>'
        f"<p>{body}</p></div>"
        for layer, title, stat, unit, body in FLOW
    )
    + "</div>"
)

SOURCE_ROWS = 35_185
ROW_OUTCOMES = [
    ("Published to Gold", "the one record kept per entity", 20_538, ""),
    (
        "Merged into a Gold record",
        "duplicates, incl. 1,065 incomplete rows we completed from a match",
        14_009,
        "",
    ),
    (
        "Held: same company, two addresses",
        "dlq_same_company_conflict",
        234,
        "is-held",
    ),
    ("Held: city or street is blank", "dlq_incomplete", 404, "is-held"),
]


def rows_html() -> str:
    top = max(n for _, _, n, _ in ROW_OUTCOMES)
    rows = []
    for label, sub, n, cls in ROW_OUTCOMES:
        width = max(n / top, 0.004)
        share = n / SOURCE_ROWS * 100
        share_txt = f"{share:.1f}%" if share >= 0.1 else "<0.1%"
        rows.append(
            f'<div class="rows-row" title="{escape(label)}: {n:,} rows ({share_txt})">'
            f'<div class="rows-label">{label}<small>{sub}</small></div>'
            f'<div class="rows-track"><div class="rows-bar {cls}" style="--w:{width:.4f}"></div>'
            f'<div class="rows-value">{n:,} <span>{share_txt}</span></div></div></div>'
        )
    return (
        '<div class="rows">'
        '<div class="rows-title">Where all 35,185 source rows ended up</div>'
        '<div class="rows-sub">From <code>silver.address_pipeline_accounting</code>. '
        "We made the run fail if these didn't add up to the source total.</div>"
        + "".join(rows)
        + "</div>"
    )


FEED_DIFFS = [
    ("Company name", "<code>company</code>", "<code>name</code>"),
    ("City", "<code>city</code>", "<code>locality</code>"),
    (
        "Region",
        "<code>state</code>, full names (Saskatchewan)",
        "<code>admin_region</code>, often codes (CT)",
    ),
    ("Country", "full names (United Kingdom)", "ISO codes (GB)"),
    ("Date", "<code>updated_at</code>", "<code>created_at</code>"),
]

feed_table = (
    '<div class="table-wrap"><table class="deck-table"><thead><tr>'
    "<th>Field</th><th>Provider A</th><th>Provider B</th></tr></thead><tbody>"
    + "".join(
        f"<tr><td>{f}</td><td class='dim'>{a}</td><td class='dim'>{b}</td></tr>"
        for f, a, b in FEED_DIFFS
    )
    + "</tbody></table></div>"
)

bronze_step = step_html(
    "Step 1 · Bronze",
    "Ingestion",
    "<p>We ingested two synthetic datasets with <strong>35,185 records</strong> "
    "(17,557 from Provider A and 17,628 from Provider B) using "
    "<strong>Auto Loader</strong>.</p>",
)

silver_step = step_html(
    "Step 2 · Silver",
    "Cleaning",
    "<p>We did basic string cleaning and merged both datasets into one canonical "
    "schema. The two providers described the same fields differently:</p>" + feed_table,
)

TIERS = [
    (
        "is-rule",
        "Deterministic",
        "1 · Lookup table",
        (
            "We translated known Chinese, Korean, and Japanese cities and provinces "
            "with a lookup table. It cost nothing and gave the same answer every time. "
            "We never replaced only part of a street address."
        ),
    ),
    (
        "is-ai",
        "AI · primary",
        "2 · Gemma 3 12B",
        (
            "We sent everything else to <code>ai_query</code>, with a prompt for each "
            "field and country group. We set temperature to 0 for repeatable answers. "
            "A full run translated all 11,929 distinct requests in about 4 minutes."
        ),
    ),
    (
        "is-rule",
        "Deterministic",
        "3 · Checks and glossary",
        (
            "We rejected answers with leftover non-Latin text, changed numbers, lost "
            "suite or building labels, or extra words. A glossary fixed recurring "
            "terms (株式会社 → Co., Ltd.) without a new AI call."
        ),
    ),
    (
        "is-ai",
        "AI · fallback",
        "4 · Qwen 3.5 122B",
        (
            "Only answers that failed the checks got a second try with the larger "
            "model. In our test it fixed 78 of 90 failures, but it was about 82× slower."
        ),
    ),
]

tiers_html = (
    '<div class="tiers">'
    + "".join(
        f'<div class="tier"><span class="tier-tag {cls}">{tag}</span>'
        f"<h4>{title}</h4><p>{body}</p></div>"
        for cls, tag, title, body in TIERS
    )
    + "</div>"
)

TRANSLATION_STATS = [
    ("8,071", "rows needed translation"),
    ("11,929", "distinct AI requests after removing repeats"),
    ("7,740", "rows accepted after translation"),
    ("7", "rows a reviewer corrected by hand"),
]


def stats_html(items: list[tuple[str, str]]) -> str:
    return (
        '<div class="stats">'
        + "".join(
            f'<div class="stat"><div class="stat-value">{v}</div>'
            f'<div class="stat-label">{label}</div></div>'
            for v, label in items
        )
        + "</div>"
    )


translation_step = step_html(
    "Step 3 · Silver",
    "Translation",
    "<p>About one in five addresses had non-Latin text: Chinese, Japanese, Korean, "
    "Russian, Thai, Hindi, Arabic. To compare records, we needed everything in one "
    "script. We went from the cheapest, most predictable method to the most "
    "expensive:</p>"
    + tiers_html
    + stats_html(TRANSLATION_STATS)
    + "<p>We accepted a translated row only if it also passed every cleaning rule. "
    "Rows that translated fine but still missed a field (331) moved on to "
    "<code>dlq_incomplete</code>. We cached responses in a Delta table keyed by "
    "the exact text, model, and prompt, so a re-run never paid for the same answer "
    "twice.</p>",
)

STAGES = [
    (
        "Deterministic",
        "Exact rule",
        (
            "Same company and the same full address after fixing case and spacing. "
            "<strong>5,559 pairs.</strong>"
        ),
    ),
    (
        "Candidates",
        "Blocking",
        (
            "Five passes grouped records that shared a key, such as country + city + "
            "building number. We only compared records in the same group. "
            "<strong>41,797 pairs.</strong>"
        ),
    ),
    (
        "Candidates",
        "Embeddings + HNSW",
        (
            "Vector search caught what keys missed: typos, reordered words, other "
            "scripts. <strong>979,677 more pairs.</strong>"
        ),
    ),
    (
        "Scoring",
        "String similarity",
        (
            "We ran Jaro–Winkler on company, cleaned street name, and city. Each gave "
            "a number from 0 to 1."
        ),
    ),
    (
        "Scoring",
        "Fellegi–Sunter",
        (
            "Splink turned those similarities into one match probability, learned "
            "without labeled data."
        ),
    ),
    (
        "Safeguards",
        "Hard conflicts",
        (
            "We parsed house number, suite, building, floor, region, and country. Any "
            "clear conflict blocked a merge, however high the score."
        ),
    ),
]

stages_html = (
    '<div class="stages">'
    + "".join(
        f'<div class="stage"><div class="stage-kind">{kind}</div>'
        f"<h4>{title}</h4><p>{body}</p></div>"
        for kind, title, body in STAGES
    )
    + "</div>"
)

MATCH_STATS = [
    ("568.4M", "possible pairs among 33,716 records"),
    ("1.02M", "pairs actually scored (0.18%)"),
    ("12,988", "pairs scored as matches (exact + model)"),
    ("14,009", "duplicate rows merged into Gold records"),
]

VS_STEPS = [
    (
        "Records",
        "We started with plain text",
        (
            "Each record was a company name plus an address. Spelling, casing, and "
            "abbreviations differed between feeds, so exact keys missed many "
            "duplicates."
        ),
    ),
    (
        "Embeddings",
        "We turned each record into a point",
        (
            "A multilingual model turned each record into 384 numbers. Records that "
            "meant the same thing landed close together, even when spelled "
            "differently. We measured closeness with <strong>cosine similarity</strong>."
        ),
    ),
    (
        "Brute force",
        "Comparing everything was too slow",
        (
            "Finding a record's neighbors by brute force meant measuring the distance "
            "to every other record. For 33,716 records, that's about "
            "<strong>568 million pairs</strong>."
        ),
    ),
    (
        "HNSW",
        "We built a layered graph",
        (
            "HNSW linked every record to its near neighbors on the bottom layer. Each "
            "layer up kept fewer records with longer links, like highways above "
            "local streets."
        ),
    ),
    (
        "Search",
        "The search went from the top layer down",
        (
            "The search started at the top and hopped to whichever linked record was "
            "closer to the target. When no hop helped, it dropped down a layer. A few "
            "hops replaced thousands of comparisons. On sampled queries, it found over "
            "99% of the neighbors an exact search found."
        ),
    ),
    (
        "Neighbors",
        "We kept the closest ones",
        (
            "We kept up to 20 new neighbors per record with cosine ≥ 0.70, skipping "
            "pairs that blocking already found. That added "
            "<strong>979,677 candidate pairs</strong>."
        ),
    ),
    (
        "Scoring",
        "We scored every candidate",
        (
            "Every candidate still went through Jaro–Winkler, Fellegi–Sunter, and the "
            "safeguards. A close neighbor could be a different suite, or a different "
            "company in the same building. Of the 979,677 vector-search pairs, "
            "<strong>26 became matches</strong>."
        ),
    ),
]

vs_steps_html = "".join(
    f'<div class="vs-step"><div class="deck-kicker">{i + 1:02d} · {kicker}</div>'
    f"<h4>{title}</h4><p>{body}</p></div>"
    for i, (kicker, title, body) in enumerate(VS_STEPS)
)

vector_search_html = (
    '<div class="vs">'
    f'<div class="vs-steps">{vs_steps_html}</div>'
    '<div class="vs-stage"><div class="vs-frame">'
    # st.html sanitizes inline <svg>, so the script draws it into this slot.
    '<div class="vs-canvas"></div>'
    '<div class="vs-legend">'
    '<span style="--c:#EB6834">Record we searched from</span>'
    '<span style="--c:#2563EB">Nearby records</span>'
    '<span style="--c:#1BAF7A">Accepted match</span>'
    '<span style="--c:#A3A8B4">Other records</span>'
    "</div>"
    '<div class="vs-caption">Illustration: about 100 dots in 2-D stand in for '
    "33,716 records in 384-D. The example records are made up.</div>"
    "</div></div></div>"
)


def evidence_rows(rows: list[tuple[str, str, float]], total: float) -> str:
    scale = 14.0  # largest |weight| maps to a full bar
    out = []
    for name, note, w in rows:
        width = min(abs(w) / scale * 50, 50)  # each side is half the track
        neg = " is-neg" if w < 0 else ""
        out.append(
            f'<div class="ev"><div class="ev-name">{name}<small>{note}</small></div>'
            f'<div class="ev-track"><div class="ev-bar{neg}" style="width:{width:.1f}%"></div></div>'
            f'<div class="ev-val">{w:+.1f}</div></div>'
        )
    out.append(
        f'<div class="ev is-total"><div>Total evidence</div><div></div>'
        f'<div class="ev-val">{total:+.1f}</div></div>'
    )
    return "".join(out)


PAIR_MERGED = (
    '<div class="pair">'
    '<div class="deck-kicker">Pair A · merged</div>'
    '<div class="pair-records">'
    '<div class="pair-record"><b>National Sonst Authority LLC</b> · Jüttnerweg 709 Ste. 734 · Gifhorn, DE</div>'
    '<div class="pair-record"><b>National Sonst Authority PLC</b> · JÜTTNERWEG 709 SUITE 734 · Gifhorn, DE</div>'
    "</div>"
    + evidence_rows(
        [
            ("Starting point", "about 1 in 100,000 random pairs match", -16.6),
            ("Company", "same once LLC / PLC are set aside", 13.2),
            ("Street name", "same after cleaning", 12.7),
            ("City", "same", 12.2),
        ],
        21.5,
    )
    + '<div class="verdict is-good">Probability <b>0.9999997</b>. House 709 and '
    "suite 734 agreed on both sides. <b>Merged.</b></div></div>"
)

PAIR_SPLIT = (
    '<div class="pair">'
    '<div class="deck-kicker">Pair B · kept apart</div>'
    '<div class="pair-records">'
    '<div class="pair-record"><b>Smith Inc</b> · Flat 6 Slater Garden - Suite 617 · New Jasonhaven, GB</div>'
    '<div class="pair-record"><b>Smith Inc</b> · Flat 6 Slater Garden Suite 926 · New Jasonhaven, GB</div>'
    "</div>"
    + evidence_rows(
        [
            ("Starting point", "about 1 in 100,000 random pairs match", -16.6),
            ("Company", "same", 13.2),
            ("Common name penalty", "lots of companies are called Smith Inc", -4.5),
            ("Street name", "same after cleaning", 12.7),
            ("City", "same", 12.2),
        ],
        17.0,
    )
    + '<div class="verdict is-bad">Probability <b>0.99999</b>, but suite 617 ≠ '
    "suite 926. A safeguard blocked it. <b>Kept as two addresses.</b></div></div>"
)

matching_step = step_html(
    "Step 4 · Matching",
    "Matching and scoring",
    "<p>We defined a duplicate as <strong>the same company at the same "
    "location</strong>. Two companies can share a building, and one company can "
    "have many offices, so we never merged records on a shared address alone.</p>"
    "<p>Comparing every record with every other would have meant 568 million "
    "pairs. Instead, we built a short list of likely pairs, scored only those, and "
    "let hard rules overrule the score.</p>"
    + stages_html
    + stats_html(MATCH_STATS)
    + "<h4>How vector search found candidates</h4>"
    + vector_search_html
    + "<h4>How we scored one pair</h4>"
    "<p>Fellegi–Sunter adds up evidence. Each field that agrees adds points, and a "
    "common value adds fewer. The total becomes a probability. These are two real "
    "pairs from our scoring run (the data is synthetic):</p>"
    '<div class="pairs">' + PAIR_MERGED + PAIR_SPLIT + "</div>"
    '<div class="rule"><p><strong>Merge rule.</strong> We merged a pair only if it '
    "had probability ≥ 0.99, Jaro–Winkler ≥ 0.85 on company, street, and city, and "
    "no safeguard conflict. Everything else was held for review or kept separate. "
    "We also never merged A with C just because A≈B and B≈C: every pair inside a "
    "group needed its own evidence.</p></div>",
    step_id="matching",
)

gold_step = step_html(
    "Step 5 · Gold",
    "Gold table",
    "<p>We turned each group of duplicates into one Gold row. We picked one real "
    "source record to represent the group and never combined fields from "
    "different records, so every Gold address existed in a source feed.</p>"
    '<ul class="deck-list">'
    "<li><strong>Which record won:</strong> the version the most sources agreed "
    "on, then one with a supplied (not inferred) country, then a stable ID as the "
    "tie-break.</li>"
    "<li><strong>Filling gaps:</strong> we completed 1,065 rows missing only a city "
    "or a street from a Gold record, but only when exactly one entity had the "
    "same company, country, and remaining address part.</li>"
    "<li><strong>Traceability:</strong> Silver kept every source row with the "
    "reason it was merged, the pair scores, and the run IDs. Gold kept the "
    "business fields and the provider key.</li>"
    "</ul>"
    "<p>The result was <code>addressresolution.gold.addresses_deduplicated</code>: "
    "<strong>20,538 addresses</strong> from 35,185 source rows.</p>",
)

DLQS = [
    (
        "<code>dlq_translate</code>",
        "Any field with non-Latin text",
        "8,071",
        "We translated them. 7,740 were accepted.",
    ),
    (
        "<code>dlq_incomplete</code>",
        "Blank, too short or long, or invalid values",
        "1,469",
        (
            "We completed 1,065 from a Gold match. 404 stayed held for the source to "
            "fix."
        ),
    ),
    (
        "<code>providers_translation_review</code>",
        "A translation failed its checks, even after the fallback",
        "0",
        "A reviewer corrected the last 7 by hand, and the pipeline applied the fixes.",
    ),
    (
        "<code>dlq_same_company_conflict</code>",
        "Same company name at addresses the matcher wouldn't merge",
        "234",
        "Held out of Gold until someone picks the true address.",
    ),
    (
        "<code>needs_match_review</code> flag",
        "A pair scored above 0.80 but a safeguard blocked it",
        "465",
        "Kept in Gold, flagged with the neighbor to compare against.",
    ),
]

dlq_table = (
    '<div class="table-wrap"><table class="deck-table"><thead><tr>'
    "<th>Queue</th><th>What went there</th><th>Rows</th><th>What we did next</th>"
    "</tr></thead><tbody>"
    + "".join(
        f"<tr><td>{q}</td><td class='dim'>{what}</td><td class='num'>{n}</td>"
        f"<td class='dim'>{nxt}</td></tr>"
        for q, what, n, nxt in DLQS
    )
    + "</tbody></table></div>"
)

dlq_step = step_html(
    "Throughout",
    "Dead letter queues",
    "<p>A <strong>dead letter queue</strong> (DLQ) is a table for rows that can't "
    "safely move forward. Instead of failing the whole pipeline or dropping data, "
    "we wrote each of those rows to a Delta table with a reason, such as "
    "<code>city:null_or_blank</code> or <code>street_address:numbers_changed</code>.</p>"
    + dlq_table
    + '<p class="deck-note">Two audit tables, <code>dlq_routing_audit</code> and '
    "<code>address_pipeline_accounting</code>, checked that every row landed in "
    "exactly one place. If the counts didn't add up, the update failed.</p>",
)

ISSUES = [
    (
        "Ingestion",
        "CSV rows split in the middle of an address",
        (
            "Street addresses contained line breaks and doubled quotes. With Spark's "
            "defaults, columns shifted."
        ),
        "We read the files in multi-line mode with RFC 4180 quote escaping.",
    ),
    (
        "Cleaning",
        "State codes in the wrong country",
        (
            "Some rows filed US states under other countries, like Maryland/MD under "
            "TR, so region checks disagreed about the same place."
        ),
        (
            "We scoped region aliases to each country, with a fallback for full name "
            "vs. code."
        ),
    ),
    (
        "Translation",
        "One prompt for every field confused the model",
        (
            "Gemma applied street rules to cities: “д. Курильск” (village "
            "of Kurilsk) became “Building 1 Kurilsk”."
        ),
        "We wrote a prompt for each field and country group, with worked examples.",
    ),
    (
        "Translation",
        "English written in Hindi or Thai script",
        (
            "The model translated the meaning or swapped in famous places: “West "
            "Vanessaport” came back as “West Vancouver”."
        ),
        (
            "We added a prompt for English-speaking countries that asked for the "
            "original spelling."
        ),
    ),
    (
        "Translation",
        "Qwen returned empty answers",
        (
            "Whenever we set a token limit, Qwen returned nothing. It was also about "
            "82× slower than Gemma."
        ),
        (
            "We removed the token cap, set temperature to 0, and used Qwen only as a "
            "fallback."
        ),
    ),
    (
        "Matching",
        "Same text, two translations",
        (
            "“森 Street” became “Mori Street” on one record and “Forest "
            "St” on another, so they looked different."
        ),
        (
            "When translations disagreed, we compared the original text. That found "
            "1,011 proposed matches."
        ),
    ),
]

issues_html = (
    '<div class="issues">'
    + "".join(
        f'<div class="issue"><div class="issue-where">{where}</div><h4>{title}</h4>'
        f'<p>{body}</p><p class="fix"><b>Fix:</b> {fix}</p></div>'
        for where, title, body, fix in ISSUES
    )
    + "</div>"
)

issues_step = step_html(
    "Lessons",
    "Problems we ran into",
    "<p>These problems changed how we built the pipeline:</p>" + issues_html,
)

approach_inner = (
    "<p>We built a <strong>medallion pipeline</strong> on Databricks. We ingested "
    "the raw feeds, cleaned and translated them, compared every record with its "
    "likely duplicates, and kept <strong>one complete address per company</strong> "
    "in the Gold table. Each step ran as a Lakeflow pipeline or job, and every "
    "table lived in Unity Catalog.</p>"
    + flow_html
    + rows_html()
    + bronze_step
    + silver_step
    + translation_step
    + matching_step
    + gold_step
    + dlq_step
    + issues_step
)

# ---------------------------------------------------------------------------
# 04 Concepts and Tools We Used
# ---------------------------------------------------------------------------

DATABRICKS_TOOLS = [
    (
        "Lakeflow Jobs",
        (
            "Runs a set of tasks in order. If one fails, “repair run” reruns only that "
            "task and the ones after it."
        ),
        (
            "One job ran Silver, then blocking → embeddings → HNSW → strings → "
            "scoring → resolution → publish."
        ),
    ),
    (
        "Lakeflow Declarative Pipelines",
        (
            "You write each table as a function. Databricks works out the order, "
            "builds the tables, and checks data-quality rules called expectations."
        ),
        (
            "We built Bronze, Silver (cleaning and translation), and output "
            "publication as pipelines. Expectations failed the run if row counts "
            "didn't add up."
        ),
    ),
    (
        "Auto Loader",
        (
            "Picks up new files from storage and remembers which ones it has already "
            "read."
        ),
        (
            "We loaded both CSV feeds into Bronze exactly once, each with an "
            "explicit all-string schema."
        ),
    ),
    (
        "Unity Catalog",
        (
            "One place to name, secure, and find data, as "
            "<code>catalog.schema.table</code>."
        ),
        (
            "We kept everything in <code>addressresolution</code>, with bronze, "
            "silver, matching, and gold schemas, plus a volume for model files."
        ),
    ),
    (
        "Delta tables",
        (
            "Data files plus a transaction log. Writes are all-or-nothing, and older "
            "versions stay readable."
        ),
        (
            "We stored every layer, every DLQ, the translation cache, and run "
            "outputs keyed by run ID as Delta tables."
        ),
    ),
    (
        "AI Functions: <code>ai_query</code>",
        "Calls an LLM from SQL or PySpark, one row at a time, inside the pipeline.",
        (
            "We translated company, street, city, and state. A bad response became "
            "an error value, not a failed run."
        ),
    ),
    (
        "AI Gateway models: Gemma and Qwen",
        "Databricks-hosted LLM endpoints behind one governed interface.",
        (
            "We used Gemma 3 12B for speed and Qwen 3.5 122B as a fallback for "
            "answers that failed our checks."
        ),
    ),
    (
        "MLflow",
        "Records each run's settings, metrics, and output files.",
        (
            "We stored the HNSW index files, the fitted Splink model, and a code hash "
            "for each run."
        ),
    ),
    (
        "Serverless compute",
        "Databricks manages the machines. You run code without setting up clusters.",
        "We ran all pipelines and jobs on serverless, in standard mode for batch runs.",
    ),
    (
        "Asset Bundles",
        "Jobs and pipelines defined as YAML files and deployed with one CLI command.",
        (
            "We deployed the matching and deduplication jobs from "
            "<code>databricks.yml</code>."
        ),
    ),
    (
        "Databricks Apps",
        "Hosts a web app next to your data, with workspace sign-in.",
        (
            "We deployed this Streamlit app on it. The app reads the Gold views "
            "through a SQL warehouse."
        ),
    ),
    (
        "Databricks SQL warehouses",
        "Serverless compute for running SQL against Unity Catalog tables.",
        (
            "We ran row-count checks, the Gemma vs. Qwen translation test, and the "
            "queries behind this app."
        ),
    ),
]

MATCHING_CONCEPTS = [
    (
        "Medallion architecture",
        (
            "Data moves through three layers: Bronze (raw), Silver (clean), and Gold "
            "(ready to use). Each layer reads only the one before it."
        ),
        "We could trace every Gold address back to its raw row.",
    ),
    (
        "Dead letter queue",
        "A holding table for rows that can't move forward yet, each with a reason.",
        (
            "We used four queues and a review flag for translation, gaps, review, and "
            "conflicts."
        ),
    ),
    (
        "Entity resolution",
        "Deciding which records describe the same real-world thing.",
        "Our “thing” was a company at one location.",
    ),
    (
        "Deterministic vs. probabilistic",
        (
            "Deterministic rules give the same answer every time and are easy to "
            "explain. Probabilistic methods weigh evidence and give a likelihood."
        ),
        (
            "We used rules first (lookups, exact match, safeguards) and models only "
            "where rules ran out."
        ),
    ),
    (
        "Blocking",
        (
            "Only compare records that share a key, like the same city and building "
            "number. This avoids comparing every pair."
        ),
        "We ran five overlapping passes, so a typo in one key didn't lose the pair.",
    ),
    (
        "Jaro–Winkler similarity",
        (
            "A 0-to-1 score for how alike two strings are. It counts shared "
            "letters and swaps, with a bonus for the same start: “MARTHA” vs. "
            "“MARHTA” is 0.96."
        ),
        (
            "We compared company, cleaned street name, and city, cut into levels like "
            "≥0.95 and ≥0.85."
        ),
    ),
    (
        "Embeddings",
        (
            "A model turns text into a list of numbers. Similar meaning gives nearby "
            "points. Cosine similarity measures the angle between them (1 = same "
            "direction)."
        ),
        (
            "We used multilingual MiniLM, 384 numbers per record, with two views: "
            "company + address, and address alone."
        ),
    ),
    (
        "HNSW",
        (
            "Hierarchical Navigable Small World: a layered graph for finding near "
            "neighbors fast. Search starts on a sparse top layer and drops down."
        ),
        (
            "We used FAISS with 32 links per node. On sampled queries, it found "
            "99.2–99.96% of the neighbors an exact search found."
        ),
    ),
    (
        "Fellegi–Sunter",
        (
            "For each field, compare how often it agrees for true matches "
            "(<em>m</em>) vs. by chance (<em>u</em>). Agreement adds "
            "log₂(m/u) points of evidence."
        ),
        (
            "We used Splink, an open-source library, to fit the model and score all "
            "1.02M candidate pairs."
        ),
    ),
    (
        "Expectation–Maximization",
        (
            "Learns the <em>m</em> values without labeled data by guessing, checking, "
            "and repeating until the answer stops changing."
        ),
        "We ran two training rounds, which settled in 13 and 8 iterations.",
    ),
    (
        "Term-frequency adjustment",
        "Agreeing on a common value is weaker evidence than agreeing on a rare one.",
        "Two “Smith Inc” records got 4.5 fewer points than two rare names would.",
    ),
    (
        "Transitive merging",
        (
            "If A matches B and B matches C, it's tempting to merge A with C. That "
            "chain can join records that don't match at all."
        ),
        (
            "We scored the missing pairs inside each group and merged only with direct "
            "evidence."
        ),
    ),
]


def cards_html(items: list[tuple[str, str, str]]) -> str:
    return (
        '<div class="deck-grid">'
        + "".join(
            f'<div class="deck-card"><h4>{name}</h4><p>{body}</p>'
            f'<p class="used"><b>How we used it:</b> {used}</p></div>'
            for name, body, used in items
        )
        + "</div>"
    )


concepts_inner = (
    "<p>Plain-language definitions of the tools and ideas behind the pipeline, "
    "and how we used each one.</p>"
    '<div class="deck-sub"><h3>Databricks tools</h3>'
    + cards_html(DATABRICKS_TOOLS)
    + "</div>"
    '<div class="deck-sub"><h3>Matching and data concepts</h3>'
    + cards_html(MATCHING_CONCEPTS)
    + "</div>"
)

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

NAV = [(s["id"], s["title"]) for s in SECTIONS] + [
    ("approach", "Our Approach"),
    ("concepts", "Concepts and Tools We Used"),
    ("demo", "Demo"),
    ("next-steps", "Next Steps"),
]
nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in NAV)

sections = "".join(
    section_html(i, s["id"], s["title"], f"<p>{s['body']}</p>")
    for i, s in enumerate(SECTIONS, start=1)
)
sections += section_html(len(SECTIONS) + 1, "approach", "Our Approach", approach_inner)
sections += section_html(
    len(SECTIONS) + 2, "concepts", "Concepts and Tools We Used", concepts_inner
)

sections += '<section class="deck-section deck-demo" id="demo"><h2>Demo</h2></section>'

NEXT_STEPS = [
    (
        "Measure accuracy with labeled pairs",
        (
            "We had no reviewed match labels, so we couldn't measure precision or "
            "recall. We'd label a sample of pairs early, including close calls like "
            "neighbors in the same building, and track both numbers on every run."
        ),
    ),
    (
        "Check the match probabilities",
        (
            "Fellegi–Sunter started from an assumed match rate, so a probability of "
            "0.99 isn't proven to mean 99%. With labels, we'd check how often each "
            "score is actually right."
        ),
    ),
    (
        "Build a review screen for held records",
        (
            "234 rows with two addresses for one company, 404 incomplete rows, and "
            "465 flagged Gold rows still need a person. We'd give reviewers a screen "
            "to pick the right answer and feed it back into the pipeline."
        ),
    ),
    (
        "Make new providers easier to add",
        (
            "Bronze reads each feed with a fixed, hand-written schema. We'd turn on "
            "schema evolution and keep unexpected columns, so a new provider or a new "
            "column doesn't need a code change."
        ),
    ),
]

next_steps_inner = (
    "<p>Things we'd change or add with more time:</p>"
    '<ul class="deck-list">'
    + "".join(
        f"<li><strong>{title}:</strong> {body}</li>" for title, body in NEXT_STEPS
    )
    + "</ul>"
)
sections += section_html(
    len(SECTIONS) + 3,
    "next-steps",
    "What We'd Do Differently / Next Steps",
    next_steps_inner,
)

script = (ASSETS / "vector_search.js").read_text(encoding="utf-8")


def logo_img(filename: str, alt: str, css_class: str) -> str:
    # st.html strips inline SVG, so embed each logo as an image data URI.
    data = base64.b64encode((ASSETS / filename).read_bytes()).decode("ascii")
    return (
        f'<img class="{css_class}" src="data:image/svg+xml;base64,{data}" alt="{alt}">'
    )


# All HTML and the script are static and authored here, so running the script
# is safe. It powers the scroll-driven vector search diagram.
st.html(
    STYLE
    + '<div class="deck">'
    + '<header class="deck-hero">'
    + '<div class="deck-logos">'
    + logo_img("altana.svg", "Altana", "logo-altana")
    + '<span class="deck-logos-x" aria-hidden="true">×</span>'
    + logo_img("databricks.svg", "Databricks", "logo-databricks")
    + "</div>"
    + "<h1>Address Resolution</h1>"
    + '<p class="deck-authors">Dharshan Vetrivelan, JJ Lee, Adam Soliman</p>'
    + f"<p>{PLACEHOLDER}</p>"
    + f'<nav class="deck-nav">{nav}</nav>'
    + "</header>"
    + sections
    + "</div>"
    + f"<script>{script}</script>",
    unsafe_allow_javascript=True,
)
