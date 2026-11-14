"""Genie Agent page: chat with the "Golden Address Resolver" Genie agent.

Genie answers take 10-60 seconds. To keep the page responsive, a question is
submitted without waiting, and a fragment checks on it every couple of seconds
until it finishes. Only the chat reruns while it waits.
"""

import base64
import logging
import os
import re
import time
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st
from databricks.sdk.service.dashboards import GenieMessage, MessageStatus

from data import workspace

# Set from the app's "genie-space" resource in app.yaml. The fallback is the
# same agent, so local runs work with your own Databricks login.
SPACE_ID = os.getenv("GENIE_SPACE_ID", "01f1deb7f3091fafa0439030d31862a2")

POLL_EVERY = "2s"
GIVE_UP_AFTER_SECONDS = 300

# Each one was checked against the live agent for a clean, demo-ready answer.
STARTER_QUESTIONS = [
    "How many addresses are there in each country? Show the top 5.",
    "How many addresses came from each provider?",
    "How many addresses are there in China, Japan, South Korea, and Russia?",
    "Show 5 addresses in Japan.",
]

LOGO = Path(__file__).parent / "views" / "assets" / "databricks.svg"

PROGRESS_LABELS = {
    MessageStatus.SUBMITTED: "Reading your question…",
    MessageStatus.FETCHING_METADATA: "Reading your question…",
    MessageStatus.FILTERING_CONTEXT: "Finding the right data…",
    MessageStatus.ASKING_AI: "Writing SQL…",
    MessageStatus.PENDING_WAREHOUSE: "Starting the SQL warehouse…",
    MessageStatus.EXECUTING_QUERY: "Running the query…",
}

FINISHED = {
    MessageStatus.COMPLETED,
    MessageStatus.FAILED,
    MessageStatus.CANCELLED,
    MessageStatus.QUERY_RESULT_EXPIRED,
}

NUMERIC_TYPES = {"BYTE", "SHORT", "INT", "LONG", "FLOAT", "DOUBLE", "DECIMAL"}

_STATE = "genie_chat"


def _state() -> dict:
    if _STATE not in st.session_state:
        st.session_state[_STATE] = {
            "conversation_id": None,
            "messages": [],
            # Set while Genie works on a question: ids, start time, progress.
            "pending": None,
        }
    return st.session_state[_STATE]


def _log_error(message: str, detail) -> str:
    """Log the full error on the server and return a short reference ID."""
    ref = uuid.uuid4().hex[:8]
    logger = logging.getLogger(__name__)
    if isinstance(detail, Exception):
        logger.error("%s (ref=%s)", message, ref, exc_info=detail)
    else:
        logger.error("%s (ref=%s): %s", message, ref, detail)
    return ref


def _error_reply(message: str, detail) -> dict:
    ref = _log_error(message, detail)
    return {"role": "assistant", "text": f"{message} Reference: `{ref}`", "error": True}


def _submit(question: str) -> None:
    state = _state()
    state["messages"].append({"role": "user", "text": question})
    try:
        if state["conversation_id"] is None:
            wait = workspace().genie.start_conversation(SPACE_ID, question)
        else:
            wait = workspace().genie.create_message(
                SPACE_ID, state["conversation_id"], question
            )
    except Exception as error:  # noqa: BLE001 - show any API failure in the chat
        state["messages"].append(
            _error_reply("Couldn't reach the agent. Try again in a moment.", error)
        )
        return

    state["conversation_id"] = wait.conversation_id
    state["pending"] = {
        "message_id": wait.message_id,
        "started": time.monotonic(),
        "steps": [PROGRESS_LABELS[MessageStatus.SUBMITTED]],
    }


def _result_table(message: GenieMessage, attachment_id: str) -> pd.DataFrame | None:
    result = (
        workspace()
        .genie.get_message_attachment_query_result(
            SPACE_ID, message.conversation_id, message.message_id, attachment_id
        )
        .statement_response
    )
    if not result or not result.manifest or not result.manifest.schema:
        return None

    columns = result.manifest.schema.columns or []
    rows = (result.result.data_array if result.result else None) or []
    table = pd.DataFrame(rows, columns=[column.name for column in columns])
    for column in columns:
        type_name = column.type_name.value if column.type_name else ""
        if type_name in NUMERIC_TYPES:
            table[column.name] = pd.to_numeric(table[column.name], errors="coerce")
    return table


def _end_lists(text: str) -> str:
    """Genie follows a list with a sentence after a single line break, which
    Markdown folds into the last bullet. Add the missing blank line."""
    return _LIST_THEN_TEXT.sub(r"\1\n\n", text)


_LIST_THEN_TEXT = re.compile(
    r"^((?:[-*+]|\d+[.)]) .*)\n(?!\s*(?:[-*+]|\d+[.)]) |\n)", re.MULTILINE
)


def _reply(message: GenieMessage) -> dict:
    if message.status != MessageStatus.COMPLETED:
        detail = message.error.error if message.error else message.status
        return _error_reply("The agent couldn't answer that. Try rephrasing.", detail)

    texts, sql, description, table, suggestions = [], None, None, None, []
    thoughts = []
    for attachment in message.attachments or []:
        if attachment.text and attachment.text.content:
            texts.append(attachment.text.content)
        if attachment.query:
            sql = attachment.query.query
            description = attachment.query.description
            thoughts = [
                thought.content
                for thought in attachment.query.thoughts or []
                if thought.content
            ]
            table = _result_table(message, attachment.attachment_id)
        if attachment.suggested_questions:
            suggestions = attachment.suggested_questions.questions or []

    return {
        "role": "assistant",
        "text": _end_lists("\n\n".join(texts))
        or description
        or "The agent had no answer.",
        "sql": sql,
        "table": table,
        "suggestions": suggestions,
        "thoughts": thoughts,
    }


def _check_pending() -> None:
    """Ask Genie once how the pending question is going."""
    state = _state()
    pending = state["pending"]
    try:
        message = workspace().genie.get_message(
            SPACE_ID, state["conversation_id"], pending["message_id"]
        )
        if message.status in FINISHED:
            reply = _reply(message)
            reply["seconds"] = round(time.monotonic() - pending["started"])
        elif time.monotonic() - pending["started"] > GIVE_UP_AFTER_SECONDS:
            reply = _error_reply(
                "The agent took too long. Try a simpler question.", message.status
            )
        else:
            label = PROGRESS_LABELS.get(message.status)
            if label and label not in pending["steps"]:
                pending["steps"].append(label)
            return
    except Exception as error:  # noqa: BLE001 - show any API failure in the chat
        reply = _error_reply("Something went wrong while getting the answer.", error)

    state["messages"].append(reply)
    state["pending"] = None


def _ask(question: str) -> None:
    st.session_state["genie_next_question"] = question


def _reset() -> None:
    st.session_state.pop(_STATE, None)


# Everything below is our own static markup. Genie output only ever goes
# through st.markdown, st.code, or st.dataframe, never unsafe_allow_html.
_CSS = """
<style>
[data-testid="stMainBlockContainer"] {
    max-width: 52rem;
    padding-bottom: 8rem;
}
.genie-brand {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.8rem 0.35rem 0.7rem;
    border: 1px solid #E6E8EE;
    border-radius: 999px;
    background: #FFFFFF;
    font-size: 0.8rem;
    font-weight: 600;
    color: #31333F;
    white-space: nowrap;
}
.genie-brand img { height: 0.85rem; display: block; }
.genie-brand span { padding-left: 0.5rem; border-left: 1px solid #E6E8EE; }
.genie-hero {
    text-align: center;
    padding: 3.5rem 0 1.75rem;
}
.genie-hero h1 {
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 1.1rem 0 0.4rem;
    padding: 0;
}
.genie-hero p {
    color: rgba(49, 51, 63, 0.65);
    max-width: 34rem;
    margin: 0 auto;
}
.genie-bar { display: flex; align-items: center; }

/* Keep the question box in view at the bottom as the chat grows. */
[data-testid="stElementContainer"]:has([data-testid="stChatInput"]) {
    position: sticky;
    bottom: 1.25rem;
    z-index: 5;
    box-shadow: 0 0 0 1.25rem #FFFFFF;
    background: #FFFFFF;
}

/* The agent's work log is secondary: smaller, quieter text. */
[data-testid="stChatMessage"] [data-testid="stExpander"] p,
[data-testid="stChatMessage"] [data-testid="stExpander"] li {
    font-size: 0.875rem;
    color: rgba(49, 51, 63, 0.8);
}
.genie-who {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: #31333F;
    margin-bottom: 0.35rem;
}
.genie-who::before {
    content: "";
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 2px;
    background: #FF3621;
    transform: rotate(45deg);
}
.genie-who small {
    font-weight: 400;
    color: rgba(49, 51, 63, 0.55);
}
.genie-steps { list-style: none; margin: 0.25rem 0 0; padding: 0; }
.genie-steps li {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0 0 0.45rem;
    font-size: 0.875rem;
    color: rgba(49, 51, 63, 0.55);
}
.genie-steps li::before {
    content: "✓";
    flex: none;
    display: grid;
    place-items: center;
    width: 1rem;
    height: 1rem;
    font-size: 0.65rem;
    color: #1BAF7A;
}
.genie-steps li.is-current { color: #31333F; }
.genie-steps li.is-current::before {
    content: "";
    width: 0.8rem;
    height: 0.8rem;
    margin: 0.1rem;
    border: 2px solid rgba(37, 99, 235, 0.25);
    border-top-color: #2563EB;
    border-radius: 50%;
    animation: genie-spin 0.8s linear infinite;
}
@keyframes genie-spin { to { transform: rotate(360deg); } }

/* Chat messages: no avatars. Questions are right-aligned bubbles. */
[data-testid="stChatMessage"] {
    padding: 0;
    gap: 0;
    background: transparent;
    margin: 0.75rem 0;
}
[data-testid^="stChatMessageAvatar"] { display: none; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    width: fit-content;
    max-width: 80%;
    margin-left: auto;
    padding: 0.65rem 1rem;
    border-radius: 1.1rem 1.1rem 0.3rem 1.1rem;
    background: #F0F2F6;
}

/* Starter prompts as cards, follow-ups as chips. */
[class*="st-key-genie_starter"] button {
    justify-content: flex-start;
    text-align: left;
    min-height: 4.75rem;
    padding: 0.9rem 1rem;
    border-radius: 0.9rem;
    border-color: #E6E8EE;
}
[class*="st-key-genie_starter"] button:hover {
    border-color: #2563EB;
    background: #F7F9FF;
}
[class*="st-key-genie_next"] button {
    border-radius: 999px;
    min-height: 0;
    padding: 0.3rem 0.85rem;
    border-color: #E6E8EE;
}
[class*="st-key-genie_next"] button p { font-size: 0.85rem; }
[class*="st-key-genie_new"] button { border-radius: 999px; }
</style>
"""


def _logo_uri() -> str:
    # st.markdown drops inline SVG, so embed the logo as an image data URI.
    return "data:image/svg+xml;base64," + base64.b64encode(LOGO.read_bytes()).decode()


def _brand() -> str:
    return (
        f'<div class="genie-brand"><img src="{_logo_uri()}" alt="Databricks">'
        "<span>Genie Agent</span></div>"
    )


def _show_work(message: dict) -> None:
    table, sql, thoughts = (
        message.get("table"),
        message.get("sql"),
        message.get("thoughts"),
    )
    if not (sql or thoughts):
        return
    seconds = message.get("seconds")
    label = f"Worked for {seconds}s" if seconds else "How I got this"
    with st.expander(label, icon=":material/manufacturing:"):
        if thoughts:
            st.markdown("**Plan**")
            for thought in thoughts:
                st.markdown(thought)
        if sql:
            st.markdown("**SQL**")
            st.code(sql, language="sql", wrap_lines=True)
        if table is not None and not table.empty:
            rows = f"{len(table):,} row{'s' if len(table) != 1 else ''}"
            st.markdown(f"**Result** · {rows}")
            st.dataframe(table, hide_index=True, width="stretch")


def _show_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["text"])
            return
        st.markdown(
            '<div class="genie-who">Genie Agent<small>· Golden Address Resolver</small></div>',
            unsafe_allow_html=True,
        )
        if message.get("error"):
            st.error(message["text"])
            return
        _show_work(message)
        st.markdown(message["text"])


def _show_progress(steps: list[str]) -> None:
    # The steps are our own PROGRESS_LABELS, never Genie output.
    items = "".join(
        f'<li class="{"is-current" if i == len(steps) - 1 else ""}">{step}</li>'
        for i, step in enumerate(steps)
    )
    with st.chat_message("assistant"):
        st.markdown(
            '<div class="genie-who">Genie Agent<small>· working</small></div>'
            f'<ul class="genie-steps">{items}</ul>',
            unsafe_allow_html=True,
        )


def _chat() -> None:
    state = _state()
    if state["pending"]:
        _check_pending()
        if not state["pending"]:
            # Done: rerun the page so the chat stops checking every 2 seconds.
            st.rerun()

    messages = state["messages"]
    pending = state["pending"]

    if not messages:
        st.markdown(
            f'<div class="genie-hero">{_brand()}'
            "<h1>Ask about the address data</h1>"
            "<p>The Golden Address Resolver agent turns your question into SQL, runs "
            "it on the Gold table, and explains the result.</p></div>",
            unsafe_allow_html=True,
        )
        left, right = st.columns(2)
        for index, question in enumerate(STARTER_QUESTIONS):
            (left if index % 2 == 0 else right).button(
                question,
                key=f"genie_starter_{index}",
                on_click=_ask,
                args=(question,),
                width="stretch",
            )
    else:
        with st.container(
            horizontal=True,
            horizontal_alignment="distribute",
            vertical_alignment="center",
        ):
            st.html(f'<div class="genie-bar">{_brand()}</div>')
            st.button(
                "New chat",
                key="genie_new",
                icon=":material/add:",
                on_click=_reset,
                disabled=bool(pending),
            )

    for message in messages:
        _show_message(message)

    if pending:
        _show_progress(pending["steps"])
    elif messages and messages[-1].get("suggestions"):
        with st.container(horizontal=True, gap="small"):
            for index, question in enumerate(messages[-1]["suggestions"]):
                st.button(
                    question,
                    key=f"genie_next_{len(messages)}_{index}",
                    on_click=_ask,
                    args=(question,),
                )

    question = st.chat_input(
        "Ask the Genie agent about the address data",
        key="genie_input",
        disabled=bool(pending),
    )
    question = question or st.session_state.pop("genie_next_question", None)

    if question and not pending:
        _submit(question)
        # Rerun the page so the chat starts checking on the answer.
        st.rerun()


def genie_chat() -> None:
    """Show the chat. Checks for an answer every 2 seconds while one is pending."""
    st.markdown(_CSS, unsafe_allow_html=True)
    run_every = POLL_EVERY if _state()["pending"] else None
    st.fragment(_chat, run_every=run_every)()
