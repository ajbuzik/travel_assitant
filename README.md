# Kraków Travel Assistant (RAG demo)

<p align="center">
  <img src="images/logo.png">
</p>

Small Retrieval-Augmented-Generation (RAG) demo that serves Points-Of-Interest (POI) recommendations for Kraków.

This project was implemented for 
[LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) -
a free course about LLMs and RAG.

## Project overview

- Streamlit UI: `travel_assistant/app.py`
- RAG backend: `travel_assistant/rag.py` (prompt building, hybrid retrieval via Qdrant, Gemini calls)
- Ingestion: `travel_assistant/ingest.py` (reads `data/krakow_pois_selected.csv`, creates Qdrant collection `hybrid_search`)

# Quick start (dev)

## Preparation

Best use what it inside .env_template file and change:
- `GEMINI_API_KEY` — required for Google Gemini calls via `google.generativeai` (used in `travel_assistant/rag.py` - main RAG model)
- `OPENAI_API_KEY` —  required for OpenAI Gemini calls via `openAI` (used in `travel_assistant/rag.py` in LLM as a Judge)
- `MISTRAL_API_KEY` - required it you want to check Notebooks used to detect model.

Call it `.env` file.
 
For dependency management, we use pipenv, so you need to install it:

```bash
pip install pipenv
```


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

* Q&A Assistant
* Monitoring

### Q&A Assistant
<p align="center">
  <img src="images/home_page.png">
</p>

Where user could write you answear. User will see conversation history and you could add feedback for each answear. User will see his feedback stats.

### Monitoring
<p align="center">
  <img src="images/monitoring.png">
</p>

To login in use `admin` and `password` or change in in  [`travel_assistant/auth.py`](travel_assistant/auth.py).

Here are monitoring statistic like:
* token usage
* costs
* LLM quality (faithfulness, groundedness, relevance, completeness, coherence, conciseness)
* User feedback sumarization

## Code 
The code for the application is in the travel_assitance folder:
* [`app.py`](travel_assistant/app.py) - main code for streanlit

