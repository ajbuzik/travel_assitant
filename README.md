# Kraków Travel Assistant (RAG demo)

<p align="center">
  <img src="images/logo.png">
</p>

Small Retrieval-Augmented-Generation (RAG) demo that serves Points-Of-Interest (POI) recommendations for Kraków.

This project was implemented for 
[LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) -
a free course about LLMs and RAG.

## Project overview

Kraków Travel Assistant is a small Retrieval-Augmented-Generation (RAG) application that helps users explore points-of-interest (POIs) in Kraków, Poland.

Main use cases
- Answer user queries about attractions, opening hours, transport, and short travel tips.
- Collect user feedback on answers to improve monitoring and quality.
- Provide admin monitoring for conversation and feedback metrics.

Key components
- Streamlit UI: travel_assistant/app.py — Q&A Assistant and Monitoring pages.
- RAG backend: travel_assistant/rag.py — prompt construction, hybrid retrieval from Qdrant, and LLM calls (Google Gemini via google.generativeai and gpt-4o-mini via OpenAI).
- Ingestion: travel_assistant/ingest.py — reads data/krakow_pois_selected.csv and creates/updates the Qdrant collection hybrid_search.
- Optional storage: Postgres (via docker-compose) for persisting conversations and feedback (helpers in travel_assistant/db.py and persistence.py).

# Quick start 

## Preparation

1. Clone repo and open project root.

2. Environment variables

- Create a `.env` from `.env_template` and set:
  - `GEMINI_API_KEY` — required for Google Gemini via `google.generativeai`.
  - `OPENAI_API_KEY` — optional (used as a judge in some flows).
  - `MISTRAL_API_KEY` — optional for notebooks.
- On Windows (PowerShell): `copy .env_template .env` then edit `.env`.
 
3. Python environment
- Pipenv:
  - pip install pipenv



## Running the application

### Running with Docker-Compose

The easiest way to run the application is with `docker-compose`:

```bash
docker-compose up
```

How it should looks if everything is correct [`docker-compose up`](images/docker_compose_up.png):

Open 'http://localhost:8501/' in your browser and enojoy application :) 

To stop the `app`:

```bash
docker-compose stop app
```

or remove it from Docker by hand :) 

### Running locally

If you want to run the application locally,
start only postgres and qdrant:

```bash
docker-compose up postgres qdrant
```

Now run the app on your host machine:

```bash
pipenv shell

streamlit run travel_assistant/app.py
```
or 

use `Run` in `Visual Studio Code`

####
Check if database is set correctly via running (only if `docker compose` up or `docker-compose up postgres qdrant` were used) :
```bash
pipenv shell

python .\travel_assistant\check_db.py
```

You should get info about Tables in database (converstion and feedback).

<p align="center">
  <img src="images/db.png">
</p>

## Using the application

There are two pages in app:

- Q&A Assistant: ask questions about Kraków POIs, see conversation history, and provide feedback.
- Monitoring: admin page showing conversation/feedback stats, token usage, and LLM quality metrics.


### Q&A Assistant
<p align="center">
  <img src="images/home_page.png">
</p>

Where user could write question and get answear. User will see conversation history and could add feedback for each answear. User will see his/her feedback stats.

### Monitoring
<p align="center">
  <img src="images/monitoring.png">
</p>

To login in use `admin` and `password` or change in   [`travel_assistant/auth.py`](travel_assistant/auth.py).

Here are monitoring statistic like:
* token usage
* costs
* LLM quality (faithfulness, groundedness, relevance, completeness, coherence, conciseness)
* User feedback sumarization

You could add tp database test cases (really poor:P) from [data/answer_data.json](travel_assistant/data/answer_data.json), [data/feedback_data.json](travel_assistant/data/feedback_data.json)

## Code

The code for the application is in the travel_assistant folder:

- [travel_assistant/app.py](travel_assistant/app.py) — Streamlit UI (Q&A Assistant & Monitoring).
- [travel_assistant/rag.py](travel_assistant/rag.py) — RAG backend: prompt building, hybrid retrieval via Qdrant, and Gemini LLM calls.
- [travel_assistant/ingest.py](travel_assistant/ingest.py) — Ingestion script: reads `data/krakow_pois_selected.csv` and creates/updates the Qdrant collection `hybrid_search`.
- [travel_assistant/auth.py](travel_assistant/auth.py) — Simple auth used by the Monitoring page.
- [travel_assistant/check_db.py](travel_assistant/check_db.py) — Helper to verify Postgres tables (conversations, feedback).
- [travel_assistant/db_prep.py](travel_assistant/db_prep.py) — DB preparation utilities.
- [travel_assistant/db.py](travel_assistant/db.py) — Database helpers used by the app and monitoring.
- [travel_assistant/persistence.py](travel_assistant/persistence.py) — Persistence layer for conversations and feedback.
- [travel_assistant/monitoring.py](travel_assistant/monitoring.py) — Monitoring page logic and stats.
- [travel_assistant/ui.py](travel_assistant/ui.py) — UI helper components for Streamlit.
- data file: [data/krakow_pois_selected.csv](travel_assistant/data/krakow_pois_selected.csv)



