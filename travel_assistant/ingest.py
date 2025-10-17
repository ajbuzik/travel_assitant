import os
import pandas as pd
from qdrant_client import models

def load_data(qdrant_client):
        
    base_dir = os.path.dirname(os.path.abspath(__file__))  # folder where ingest.py is
    data_path = os.path.join(base_dir, "data", "krakow_pois_selected.csv")
    
    poi_data = pd.read_csv(data_path)
    documents = poi_data.to_dict(orient='records')

    

    if qdrant_client.collection_exists(collection_name="hybrid_search"):
        qdrant_client.delete_collection("hybrid_search")

    
    qdrant_client.create_collection(
        collection_name="hybrid_search",
        vectors_config={
            # Named dense vector for jinaai/jina-embeddings-v2-small-en
            "jina-small": models.VectorParams(
                size=512,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            )
        }
)

    qdrant_client.upsert(
collection_name="hybrid_search",
points=[
    models.PointStruct(
        id=doc['id'],
        vector={
            "jina-small": models.Document(
                text=doc['name'] + ' ' + doc['amenity'] + ' ' + doc['leisure'] + ' ' + doc['natural'] + ' ' + doc['tourism'] + ' ' + doc['historic'] + ' ' + doc['wiki_summary_en'],
                model="jinaai/jina-embeddings-v2-small-en",
            ),
            "bm25": models.Document(
                text=doc['name'] + ' ' + doc['amenity'] + ' ' + doc['leisure'] + ' ' + doc['natural'] + ' ' + doc['tourism'] + ' ' + doc['historic'] + ' ' + doc['wiki_summary_en'],
                model="Qdrant/bm25",
            ),
        },
        payload={
            "name": doc['name'],
        "wiki_summary_en": doc['wiki_summary_en'],
        'id'    : doc['id'],
        }
    )
    for doc in documents
]
)
    return documents,qdrant_client