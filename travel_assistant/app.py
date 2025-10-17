import os
import uuid
import datetime
from typing import Tuple, List
import streamlit as st
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import google.generativeai as genai

import ui
import monitoring
import persistence
import ingest

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

st.set_page_config(page_title="Krakow Travel Assistant", page_icon="🤖", layout="wide")

# --- Session / constants -----------------------------------------------------
def init_session_state() -> None:
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'feedback_data' not in st.session_state:
        st.session_state.feedback_data = []
    # keep 'previous_answer' key if other modules expect it
    if 'previous_answer' not in st.session_state:
        st.session_state.previous_answer = None

init_session_state()

# --- Cached resources -------------------------------------------------------
@st.cache_resource
def get_qdrant_client(url: str = QDRANT_URL) -> QdrantClient:
    return QdrantClient(url=url)

@st.cache_resource
def load_documents_and_client(_qdrant_client: QdrantClient) -> Tuple[List[dict], QdrantClient]:
    DOCUMENTS, client = ingest.load_data(_qdrant_client)
    return DOCUMENTS, client

# --- Main app navigation ----------------------------------------------------
def main() -> None:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", ["Q&A Assistant", "Monitoring"])

    qdrant = get_qdrant_client()
    DOCUMENTS, qdrant_client = load_documents_and_client(qdrant)

    if page == "Q&A Assistant":
        ui.qa_page(DOCUMENTS, qdrant_client, OPENAI_API_KEY)
    else:
        monitoring.monitoring_page()

if __name__ == "__main__":
    main()