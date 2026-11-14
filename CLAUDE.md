# CLAUDE.md

Guidance for coding agents working in this repo. `AGENTS.md` is a symlink to this file.

## What this is

A Streamlit app, deployed with Databricks Apps, for the Tech@NYU × Databricks × Altana address resolution project. The pipeline itself (Bronze → Silver → Matching → Gold) lives in the Databricks workspace, not here. This app reads its results.

Three pages, wired up in `app.py`:

- **Entity Explorer** (`views/explorer.py`): reads the Gold views through a SQL warehouse (`data.py`). Read-only.
- **Genie Agent** (`views/agent.py`, logic and styles in `genie_chat.py`): a full-page chat with the "Golden Address Resolver" Databricks Genie agent. Each answer shows the agent's plan, SQL, and result in a "Worked for Ns" expander.
- **Presentation** (`views/presentation.py`): a scrolling write-up of the project for the final presentation. Sections: The Problem, Why It Matters, Our Approach, Concepts and Tools We Used. All its content is static HTML written in Python. It does not query anything at runtime.

All project data is synthetic. Live tables are in the `addressresolution` Unity Catalog.

## Presentation copy rules

- Write in past tense, using "we" ("We ingested…", "We merged…"). General definitions of a tool or concept can stay in present tense ("Auto Loader picks up new files…"). How we used it stays in past tense.
- Use simple words and short sentences. Give a brief plain definition for any complex term.
- No catchy, AI-sounding taglines or slogans (for example "park it, don't drop it", "rules first, AI second"). Use plain section titles.
- Keep the ingestion and cleaning parts short.
- Only state facts we can back up. The numbers are hard-coded from the live workspace tables and one scoring run. They do not update when the pipeline reruns, so re-check them against the workspace before changing them, and don't invent new ones.

## `st.html` and the scroll animation

The Approach section has a scroll-driven embeddings/HNSW diagram. Its script is in `views/assets/vector_search.js`, and the page loads it with `st.html(..., unsafe_allow_javascript=True)`. That is safe only because all the HTML and JS is our own static content. Never put feed data or user input into this page.

Things that break it:

- `st.html` does not use an iframe. It cleans the markup with DOMPurify, which removes inline `<svg>`. So the script builds the SVG itself, inside the `.vs-canvas` slot.
- DOMPurify drops the whole `<script>` if its text contains anything tag-like: `<` followed by a letter or `/`, even inside a comment or string. The JS file must never contain that. Check with `grep -cP '<[/\w]' views/assets/vector_search.js`, which must print `0`.
- The script can run before its root element is attached, so it retries until the root appears. It also cleans up after itself when the root is removed.
- Streamlit scrolls the inner `[data-testid=stMain]` container, not the window. Listen for scroll in the capture phase on `document`. `position: sticky` works.
- Monospace fonts lack CJK and Cyrillic glyphs. Write non-Latin examples as quoted text, not `<code>`.
- Logos (`views/assets/altana.svg`, `views/assets/databricks.svg`) are the companies' official header SVGs. Because inline SVG is stripped, they're embedded as `<img>` data URIs.

## Genie chat

- The app reaches the agent through its `genie-space` app resource (Can run), which `app.yaml` maps to `GENIE_SPACE_ID`. The agent queries `addressresolution.gold.addresses_deduplicated`, so the app's service principal needs `SELECT` on it.
- Answers take 10-60 seconds. Don't block on them: the question is submitted without waiting, and a fragment with `run_every` checks once every 2 seconds while one is pending. Blocking would freeze the page.
- Show Genie errors as a short message with a reference ID and log the details. Don't show raw API errors to users.
- Genie's text is Markdown. Render it with `st.markdown`, never with `unsafe_allow_html`. Only our own static markup (brand pill, progress steps) uses HTML.

## Layout

- All page text is center-aligned, and paragraphs span up to `60rem`. The exceptions are charts, where alignment carries meaning: the row-accounting bars, the evidence bars in the scored pairs, and the scroll diagram's step text.
- Streamlit's own CSS pads lists and other elements. Reset them with `!important` where needed.

## Checks

- Lint: `ruff check .` and `ruff format --check .`. The `.venv` ruff is newer and also enforces ISC004, so wrap multi-line implicit string concatenations inside tuples and lists in parentheses.
- JS: `node --check views/assets/vector_search.js`, plus the tag-like-text grep above.
- Run the app with `.venv/bin/streamlit run app.py`, then open `/presentation`. Check it at desktop and phone widths (about 390 px). Scroll through every step of the diagram, and confirm there's no horizontal overflow and no new console errors. Two `_stcore` 404s when you load `/presentation` directly are expected.

## Rules

- Don't change workspace paths or Unity Catalog table names in code.
- Don't sync, start, or edit teammates' pipelines in the workspace.
- Commit, push, or deploy only when asked.
