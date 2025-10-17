### Repository shortcuts for AI coding agents

This file gives focused, actionable guidance for automated coding agents working on the Kraków Travel Assistant project.

Keep it short and specific: modify only when the codebase layout, major services, or runtime commands change.

1) Big picture
- Purpose: a small Retrieval-Augmented-Generation (RAG) app that serves POI (points-of-interest) recommendations for Kraków.
- Components:
  - Streamlit UI: `travel_assistant/app.py` (single-file Streamlit app used for manual testing and demos).
  - RAG backend logic: `travel_assistant/rag.py` (builds prompts, performs hybrid retrieval via Qdrant, calls Gemini via `google.generativeai`).
  - Ingestion & storage: `travel_assistant/ingest.py` (reads `data/krakow_pois_selected.csv`, creates/uses Qdrant collection `hybrid_search`).
  - Optional database: `docker-compose.yml` defines Postgres + pgAdmin used mainly for feedback storage scripts (see `postgres_init_script.py` and `setup_database.ps1`).

2) Entrypoints & quick dev commands
- Run Streamlit UI (default dev): from repo root
  - powershell: `streamlit run travel_assistant/app.py`
- Local Qdrant is expected at `http://localhost:6333`. The ingest script uses that endpoint.
  - Quick local Qdrant (docker): `docker run -p 6333:6333 -p 6334:6334 -v "${PWD}\qdrant_storage:/qdrant/storage" qdrant/qdrant`
- Postgres stack (feedback storage): `docker-compose up -d` will bring up `postgres` and `pgadmin` as defined in `docker-compose.yml`.
- Python environment: repo uses Pipfile (pipenv). You can also use pip with `requirements_file.txt` in `travel_assistant/`.

3) Important environment variables
- `GEMINI_API_KEY` — used in `travel_assistant/rag.py` to call Google Gemini via `google.generativeai`. Set in OS or `.env`.
- `OPENAI_API_KEY` — mentioned in README; not used directly in current code, but may exist in notebooks or future branches.

4) Project-specific patterns & conventions
- RAG flow: query → `rrf_search()` (Qdrant Fusion RRF with prefetch) → `filter_rrf_results()` → `build_context()` → LLM call `gemini_llm()` in `rag.py`.
  - The system stores hybrid vectors named `jina-small` and sparse BM25 in collection `hybrid_search` (see `ingest.py`).
- Data shape: ingestion reads CSV `data/krakow_pois_selected.csv` and converts to list-of-dicts. Each document payload contains `id`, `name`, and `wiki_summary_en`. The prompt template expects many POI fields — use `entry_template` in `rag.py` when creating context.
- State management in Streamlit: `travel_assistant/app.py` relies on `st.session_state` keys: `conversation_history`, `feedback_data`, and `previous_answer` (set by `rag.rag`). Be careful when refactoring those names.

5) Common errors & troubleshooting
- Qdrant connectivity: `ConnectionRefusedError` or empty query results usually mean no local Qdrant. Start the docker container above.
- Vector migration/OutputTooSmall: large errors from Qdrant or model SDK (for example the 500/OutputTooSmall panic) often come from mismatched vector size, wrong payload shape, or using a model/document type incompatible with the SDK. Check `ingest.py` for vector configs and ensure `size=512` matches the embedder used.
- Gemini API issues: `google.generativeai` requires `genai.configure(api_key=...)` and the proper model name (`gemini-2.5-flash-lite` is used). If LLM calls fail with 500, inspect network, API key, and prompt length. The code appends previous answers to context — guard prompt size.

6) Small, concrete examples for edits
- Add a field to the prompt context: update `entry_template` in `travel_assistant/rag.py` and ensure `ingest.py` payload contains that field. Update `build_context()` formatting accordingly.
- Change the embedding model: update `model_handle` and `vectors_config` size in `travel_assistant/ingest.py`. If size changes, update `EMBEDDING_DIMENSIONALITY` and Qdrant vector config.
- Improve robustness around empty responses: wrap `gemini_llm()` result access (candidates/parts) to avoid IndexError; add a timeout/retry around external calls.

7) Files to inspect when changing behavior
- `travel_assistant/ingest.py` — data loading and Qdrant collection creation/upsert
- `travel_assistant/rag.py` — all retrieval, prompt building and LLM calls
- `travel_assistant/app.py` — Streamlit UI, session state keys, and feedback saving
- `data/*.csv` — source POI datasets and `data/experiments_output/` contains historical outputs
- `docker-compose.yml` and `setup_database.ps1` — local infra for Postgres/pgAdmin

8) Style and testing notes
- There are no unit tests in the repository. Small changes should be validated by running the Streamlit UI locally and exercising the RAG path (submit a question and confirm a response).
- Keep the Streamlit app small and synchronous — refactors that introduce async behavior may require changing how `st.spinner()` and `st.session_state` are used.

9) When in doubt
- Re-run `travel_assistant/ingest.py` as a module in an interactive REPL to inspect `documents` returned from CSV.
- Search for `previous_answer` and `hybrid_search` when tracking state and storage.

If anything here is unclear or you'd like more concrete examples (unit tests, CI steps, or CI configuration), tell me which area to expand and I'll iterate.
