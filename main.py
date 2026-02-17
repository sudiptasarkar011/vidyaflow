import streamlit as st
import os
from dotenv import load_dotenv
from src.agent import ResearchAgent

# Load Env
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    st.error("⚠️ GOOGLE_API_KEY missing.")
    st.stop()

st.set_page_config(page_title="VidyaFlow", page_icon="🧠", layout="wide")

@st.cache_resource
def get_agent():
    return ResearchAgent()

agent = get_agent()

# Sidebar
with st.sidebar:
    st.title("⚙️ VidyaFlow Config")
    st.info("Architecture: Hybrid (Qdrant + Gemini)")
    mode = st.radio("Mode", ["Quick Mode", "Deep Mode"])
    mode_key = "quick" if "Quick" in mode else "deep"
    st.divider()
    st.metric(label="Memory Engine", value="Qdrant", delta="Active")

# Main
st.title("🧠 VidyaFlow")
st.markdown("### *Production-Grade Technical Research Agent*")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Enter technical query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Processing in {mode_key.upper()} mode..."):
            result = agent.generate_response(prompt, mode=mode_key)
            
            if result["status"] == "success":
                st.markdown(result["content"])
                
                # Dynamic Footer based on Source
                if result.get("source") == "memory":
                    st.success(f"⚡ Retrieved from Qdrant Memory | Cost: $0.00 | Latency: <0.1s")
                else:
                    st.info(f"🌐 Fresh Research | Tokens: {result['tokens']} | Cost: ${result['cost']}")
                
                st.session_state.messages.append({"role": "assistant", "content": result["content"]})
            else:
                st.error(f"Error: {result['message']}")