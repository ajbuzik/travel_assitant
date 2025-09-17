# travel_assitant
**Krakow Travel Assistant** is an intelligent, AI-powered application designed to help you explore and experience the best of Krakow. Leveraging Retrieval-Augmented Generation (RAG) and advanced language models, this assistant provides personalized recommendations, answers travel-related questions, and helps you plan your visit with ease. Whether you're looking for historical sites, local cuisine, or hidden gems, the Krakow Travel Assistant is your go-to companion for discovering the city.
## Features

- Retrieval-Augmented Generation (RAG) architecture
- Integrates with OpenAI LLMs for natural language responses
- Custom document ingestion and retrieval pipeline
- FastAPI backend for API endpoints
- Streamlit-based web UI for user interaction

## Installation

```bash
git clone https://github.com/yourusername/travel_assitant.git
cd travel_assitant
pip install -r requirements.txt
```

## Usage

1. **Start the backend API:**
    ```bash
    uvicorn app.main:app --reload
    ```
2. **Launch the Streamlit UI:**
    ```bash
    streamlit run ui/app.py
    ```

## Configuration

- Set your OpenAI API key in the `.env` file:
  ```
  OPENAI_API_KEY=your_api_key_here
  ```

## Project Structure

```
travel_assitant/
├── app/                # FastAPI backend
│   ├── main.py
│   └── ...
├── ui/                 # Streamlit frontend
│   └── app.py
├── data/               # Sample documents
├── requirements.txt
└── README.md
```

## Ingestion

## Evaluation

## Retrieval



## License

MIT License

## Acknowledgements

- [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp)
- [OpenAI](https://openai.com/)
- [Streamlit](https://streamlit.io/)