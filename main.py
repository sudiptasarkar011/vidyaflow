import os
import json
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from src.agent import ResearchAgent

# Load Env
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    st.error("GOOGLE_API_KEY missing.")
    st.stop()

st.set_page_config(page_title="VidyaFlow", layout="wide")

HISTORY_PATH = Path("chat_history.json")


def load_history():
    """Load all conversations from disk.

    Supports both the new multi-chat format and the older
    single-chat list-of-messages format.
    """
    if not HISTORY_PATH.exists():
        return {"chats": [], "active_id": None}

    try:
        data = json.loads(HISTORY_PATH.read_text())
    except Exception:
        return {"chats": [], "active_id": None}

    # Old format: plain list of messages
    if isinstance(data, list):
        chat_id = str(uuid4())
        return {
            "chats": [
                {
                    "id": chat_id,
                    "title": "Chat 1",
                    "messages": data,
                }
            ],
            "active_id": chat_id,
        }

    # New format
    chats = data.get("chats", [])
    active_id = data.get("active_id")
    if not isinstance(chats, list):
        return {"chats": [], "active_id": None}

    return {"chats": chats, "active_id": active_id}


def save_history():
    """Persist all conversations to disk."""
    try:
        payload = {
            "chats": st.session_state.get("chats", []),
            "active_id": st.session_state.get("active_chat_id"),
        }
        HISTORY_PATH.write_text(json.dumps(payload, indent=2))
    except Exception:
        pass


def get_active_chat():
    chats = st.session_state.get("chats", [])
    active_id = st.session_state.get("active_chat_id")

    for chat in chats:
        if chat.get("id") == active_id:
            return chat

    return chats[0] if chats else None

@st.cache_resource
def get_agent():
    return ResearchAgent()

agent = get_agent()

# Conversations state
history = load_history()

if "chats" not in st.session_state:
    st.session_state.chats = history["chats"]
    st.session_state.active_chat_id = history["active_id"]

if not st.session_state.chats:
    first_id = str(uuid4())
    st.session_state.chats = [{"id": first_id, "title": "Chat 1", "messages": []}]
    st.session_state.active_chat_id = first_id

# Sidebar
with st.sidebar:
    st.markdown("### VidyaFlow")
    st.caption("Hybrid technical research agent")

    chats = st.session_state.chats

    # Conversations section
    st.markdown("#### Chats")

    chat_ids = [chat["id"] for chat in chats]
    title_lookup = {chat["id"]: chat["title"] for chat in chats}

    current_id = st.session_state.get("active_chat_id") or chat_ids[0]
    if current_id not in chat_ids:
        current_id = chat_ids[0]

    selected_id = st.radio(
        "Chats",
        options=chat_ids,
        index=chat_ids.index(current_id),
        format_func=lambda cid: title_lookup.get(cid, "Untitled"),
        label_visibility="collapsed",
        key="chat_selector",
    )

    st.session_state.active_chat_id = selected_id

    # Rename current chat
    active_chat = next((c for c in chats if c["id"] == selected_id), chats[0])
    new_title = st.text_input(
        "Chat name",
        value=active_chat["title"],
        key=f"chat_title_input_{active_chat['id']}",
    )
    if st.button("Save name", use_container_width=True, key=f"save_title_{active_chat['id']}"):
        title = new_title.strip()
        if title:
            active_chat["title"] = title
            save_history()

    col_new, col_clear = st.columns(2)
    with col_new:
        if st.button("New chat", use_container_width=True):
            new_id = str(uuid4())
            new_title = f"Chat {len(chats) + 1}"
            new_chat = {"id": new_id, "title": new_title, "messages": []}
            st.session_state.chats.append(new_chat)
            st.session_state.active_chat_id = new_id
            active_chat = new_chat
            save_history()
    with col_clear:
        if st.button("Clear chat", use_container_width=True):
            active_chat["messages"].clear()
            save_history()

    st.divider()

    # Mode section
    st.markdown("#### Mode")
    mode = st.radio(
        "Mode",
        ["Quick", "Deep"],
        horizontal=False,
    )
    mode_key = "quick" if mode == "Quick" else "deep"
    st.caption("Quick: shorter answers · Deep: thorough breakdown")

    st.divider()
    st.caption("Memory engine: Qdrant (local)")

# Main
st.markdown("## VidyaFlow")
st.caption("Production-grade technical research for engineers")

active_chat = get_active_chat()
if active_chat is None:
    first_id = str(uuid4())
    active_chat = {"id": first_id, "title": "Chat 1", "messages": []}
    st.session_state.chats = [active_chat]
    st.session_state.active_chat_id = first_id
    save_history()

messages = active_chat["messages"]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Enter technical query..."):
    messages.append({"role": "user", "content": prompt})

    # Simple title from first user message
    if active_chat["title"].startswith("Chat ") and len(messages) == 1:
        short_title = prompt.strip().split("\n")[0][:40]
        if len(prompt.strip()) > 40:
            short_title += "…"
        active_chat["title"] = short_title or active_chat["title"]

    save_history()
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Processing in {mode_key.upper()} mode..."):
            result = agent.generate_response(prompt, mode=mode_key)

            if result["status"] == "success":
                st.markdown(result["content"])

                # Compact dynamic footer based on source
                source = result.get("source")
                if source == "memory":
                    st.caption("Memory result · Qdrant · cost $0.00 · latency <0.1s")
                else:
                    st.caption(f"Fresh research · tokens {result['tokens']} · cost ${result['cost']}")

                messages.append({"role": "assistant", "content": result["content"]})
                save_history()
            else:
                st.error(f"Error: {result['message']}")