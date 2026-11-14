"""Sidebar chat with the "Golden Address Resolver" Genie agent.

Genie answers take 10-60 seconds. To keep the page responsive, a question is
submitted without waiting, and a fragment checks on it every couple of seconds
until it finishes. Only the chat reruns while it waits, not the whole page.
"""

import logging
import os
import re
import time
import uuid

import pandas as pd
import streamlit as st
from databricks.sdk.service.dashboards import GenieMessage, MessageStatus

from data import workspace

# Set from the app's "genie-space" resource in app.yaml. The fallback is the
# same agent, so local runs work with your own Databricks login.
SPACE_ID = os.getenv("GENIE_SPACE_ID", "01f1deb7f3091fafa0439030d31862a2")

POLL_EVERY = "2s"
GIVE_UP_AFTER_SECONDS = 300

STARTER_QUESTIONS = [
    "How many unique addresses are there by country? Top 5.",
    "What are the top 5 cities with the most unique addresses?",
]

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
        "label": PROGRESS_LABELS[MessageStatus.SUBMITTED],
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
    for attachment in message.attachments or []:
        if attachment.text and attachment.text.content:
            texts.append(attachment.text.content)
        if attachment.query:
            sql = attachment.query.query
            description = attachment.query.description
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
        elif time.monotonic() - pending["started"] > GIVE_UP_AFTER_SECONDS:
            reply = _error_reply(
                "The agent took too long. Try a simpler question.", message.status
            )
        else:
            pending["label"] = PROGRESS_LABELS.get(message.status, pending["label"])
            return
    except Exception as error:  # noqa: BLE001 - show any API failure in the chat
        reply = _error_reply("Something went wrong while getting the answer.", error)

    state["messages"].append(reply)
    state["pending"] = None


def _ask(question: str) -> None:
    st.session_state["genie_next_question"] = question


def _reset() -> None:
    st.session_state.pop(_STATE, None)


def _show_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["text"])
            return
        st.markdown(message["text"])
        table = message.get("table")
        if table is not None and not table.empty:
            rows = f"{len(table):,} row{'s' if len(table) != 1 else ''}"
            with st.expander(f"Data · {rows}"):
                # Numbers are right-aligned. In the narrow sidebar a column
                # sized to its long header pushes them out of view.
                st.dataframe(
                    table,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        name: st.column_config.NumberColumn(
                            name.replace("_", " "), width="small", help=name
                        )
                        if pd.api.types.is_numeric_dtype(table[name])
                        else st.column_config.TextColumn(name.replace("_", " "))
                        for name in table.columns
                    },
                )
        if message.get("sql"):
            with st.expander("SQL"):
                st.code(message["sql"], language="sql", wrap_lines=True)


def _suggestion_buttons(questions: list[str], key: str) -> None:
    for index, question in enumerate(questions):
        st.button(
            question,
            key=f"{key}_{index}",
            on_click=_ask,
            args=(question,),
            width="stretch",
        )


def _chat() -> None:
    state = _state()
    if state["pending"]:
        _check_pending()
        if not state["pending"]:
            # Done: rerun the page so the chat stops checking every 2 seconds.
            st.rerun()

    messages = state["messages"]
    if not messages:
        st.caption(
            "Ask a question about the Gold address data. Answers take up to a minute."
        )
        _suggestion_buttons(STARTER_QUESTIONS, "genie_starter")

    for message in messages:
        _show_message(message)

    if state["pending"]:
        with st.chat_message("assistant"):
            # The label is one of our own PROGRESS_LABELS, never Genie output.
            st.markdown(
                f'<div class="genie-progress">{state["pending"]["label"]}</div>',
                unsafe_allow_html=True,
            )
    elif messages and messages[-1].get("suggestions"):
        _suggestion_buttons(messages[-1]["suggestions"], f"genie_next_{len(messages)}")

    question = st.chat_input(
        "Ask about the data", key="genie_input", disabled=bool(state["pending"])
    )
    question = question or st.session_state.pop("genie_next_question", None)

    if messages:
        st.button(
            "New chat",
            on_click=_reset,
            disabled=bool(state["pending"]),
            width="stretch",
        )

    if question and not state["pending"]:
        _submit(question)
        # Rerun the page so the chat starts checking on the answer.
        st.rerun()


def genie_chat() -> None:
    """Show the chat. Checks for an answer every 2 seconds while one is pending."""
    run_every = POLL_EVERY if _state()["pending"] else None
    st.fragment(_chat, run_every=run_every)()
