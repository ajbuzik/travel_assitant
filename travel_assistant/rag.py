import pandas as pd
from qdrant_client import models
import google.generativeai as genai
import streamlit as st

ENTRY_TEMPLATE = """

phone : {phone}
cemetery : {cemetery}
emergency : {emergency}
opening_hours : {opening_hours}
website : {website}
pets_allowed : {pets_allowed}
geometry : {geometry}
historic : {historic}
wiki_summary_en : {wiki_summary_en}
postal_code : {postal_code}
toilets : {toilets}
natural : {natural}
description : {description}
visiting_time : {visiting_time}
leisure : {leisure}
tourism : {tourism}
public_transport : {public_transport}
brand : {brand}
alt_name : {alt_name}
amenity : {amenity}
reservation : {reservation}
attraction : {attraction}
highchair : {highchair}
parking : {parking}
swimming_pool : {swimming_pool}
contact_phone : {contact_phone}
community_centre : {community_centre}
addr_street : {addr_street}
contact_twitter : {contact_twitter}
social_facility : {social_facility}
contact_facebook : {contact_facebook}
zoo : {zoo}
email : {email}
wheelchair : {wheelchair}
cuisine : {cuisine}
contact_website : {contact_website}
internet_access : {internet_access}
opening_hours_reception : {opening_hours_reception}
guest_house : {guest_house}
addr_city : {addr_city}
contact_instagram : {contact_instagram}
image : {image}
location : {location}
outdoor_seating : {outdoor_seating}
museum : {museum}
takeaway : {takeaway}
smoking : {smoking}
name : {name}
id : {id} """.strip()


PROMPT_TEMPLATE = """### You are a Kraków Travel Assistant specialized in Points of Interest (POIs). Your goal is to provide accurate, actionable, 
    and personalized recommendations using context data.

Always aim to help the user explore Kraków efficiently and enjoyably, focusing on the most relevant and high-value POIs.

QUESTION: {question}

CONTEXT: {context}

Answer:"""



def rrf_search(qdrant_client,query: str, limit: int = 1) -> list[models.ScoredPoint]:
    results = qdrant_client.query_points(
        collection_name="hybrid_search",
        prefetch=[
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="jinaai/jina-embeddings-v2-small-en",
                ),
                using="jina-small",
                limit=(5 * limit),
            ),
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="Qdrant/bm25",
                ),
                using="bm25",
                limit=(5 * limit),
            ),
        ],
        # Fusion query enables fusion on the prefetched results
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True,
    )

    return results.points

def build_context(search_results,entry_template):
    
    context = ""
    
    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"
    
    return context

def build_prompt(prompt_template, query, context):
    
    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

def filter_rrf_results(results,documents):
    context_selected_ids = []
    for record in results:
        context_selected_ids.append(record.id)
    return [doc for doc in documents if doc["id"] in context_selected_ids]

def gemini_llm(prompt):
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content(
        prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.0
            )
    )
    if response.candidates and response.candidates[0].content.parts:
        return response.candidates[0].content.parts[0].text
    else:
          return ""
    

def rag(st,query,DOCUMENTS, qdrant_client, prompt_template = PROMPT_TEMPLATE,entry_template = ENTRY_TEMPLATE):
    if 'previous_answer' not in st.session_state:
        st.session_state.previous_answer = None
    search_results = rrf_search(qdrant_client, query)
    search_results =filter_rrf_results(search_results, DOCUMENTS)
    context = build_context(search_results,entry_template)

    if st.session_state.previous_answer:
        context += f"\n\nPrevious answer:\n{st.session_state.previous_answer}"
    
    prompt = build_prompt(prompt_template,query, context)
    answer = gemini_llm(prompt)

    st.session_state.previous_answer = answer
    return answer



