# Kraków Travel Assistant (RAG demo)

Small Retrieval-Augmented-Generation (RAG) demo that serves Points-Of-Interest (POI) recommendations for Kraków.
Project overview
## Quick overview
- Streamlit UI: `travel_assistant/app.py`
- RAG backend: `travel_assistant/rag.py` (prompt building, hybrid retrieval via Qdrant, Gemini calls)
- Ingestion: `travel_assistant/ingest.py` (reads `data/krakow_pois_selected.csv`, creates Qdrant collection `hybrid_search`)
- Optional Postgres (feedback): configured in `docker-compose.yml`

## Quick start (dev)
1. Install deps
   - Pipenv: `pipenv install` or use pip with `travel_assistant/requirements_file.txt`.
2. Start local Qdrant (required for retrieval):
   - PowerShell:
     ```
     docker run -p 6333:6333 -p 6334:6334 -v "${PWD}\qdrant_storage:/qdrant/storage" qdrant/qdrant
     ```
3. (Optional) Start Postgres + pgAdmin:
   ```
   docker-compose up -d
   ```
4. Run Streamlit UI (from repo root):
   - PowerShell:
     ```
     streamlit run travel_assistant/app.py
     ```
5. Ingest data into Qdrant (if collection not present):
   ```
   python -m travel_assistant.ingest
   ```
   or
   ```
   python travel_assistant\ingest.py
   ```

## Environment variables
- `GEMINI_API_KEY` — required for Google Gemini calls via `google.generativeai` (used in `travel_assistant/rag.py`)
- `OPENAI_API_KEY` — referenced in README but not used by current code

Set env vars in OS or a `.env` file prior to running.

## Important details & conventions
- Qdrant collection: `hybrid_search` (stores dense vectors named `jina-small` and sparse BM25 payloads).
- Session state keys used by Streamlit app: `conversation_history`, `feedback_data`, `previous_answer`
- RAG flow in `travel_assistant/rag.py`:
  - `rrf_search()` → `filter_rrf_results()` → `build_context()` → `gemini_llm()`
- CSV source: `data/krakow_pois_selected.csv` (documents contain `id`, `name`, `wiki_summary_en`, etc.)
- Embedding dimensionality and vector config must match between embedder and Qdrant (`ingest.py`).

## Troubleshooting
- ConnectionRefusedError / empty results: ensure Qdrant is running at `http://localhost:6333`.
- Gemini API errors (500/timeout): verify `GEMINI_API_KEY`, model name in `rag.py`, and prompt length.
- Vector size mismatch: check `vectors_config` size in `travel_assistant/ingest.py` and embedding model used.

## Files to inspect when changing behavior
- `travel_assistant/ingest.py`
- `travel_assistant/rag.py`
- `travel_assistant/app.py`
- `data/*.csv`

## Notes
- Keep Streamlit app synchronous to preserve `st.session_state` behavior.
- There are no unit tests in the repo; validate changes by running the Streamlit app and the ingest pipeline.