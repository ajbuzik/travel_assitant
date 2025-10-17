import pandas as pd
from qdrant_client import models
import google.generativeai as genai
import streamlit as st
from openai import OpenAI
import re
import json


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
        answer_text = response.candidates[0].content.parts[0].text
        
        metadata = getattr(response, "usage_metadata", {})

        token_count = metadata.total_token_count
        input_tokens = metadata.prompt_token_count
        model_name = response.model_version


        cost = None
        if token_count is not None:
        
            cost = token_count / 1_000_000 * 0.4

        return {
        "answer": answer_text,
        "tokens_used": token_count,
        "input_tokens": input_tokens,
        "estimated_cost_usd": cost,
        "model_name": model_name,
        }
    else:
        return {
        "answer": "",
        "tokens_used": None,
        "input_tokens": None,
        "estimated_cost_usd": None,
        "model_name": None,
        }
    

def rag(st,query,DOCUMENTS, qdrant_client,OPENAI_API_KEY, prompt_template = PROMPT_TEMPLATE,entry_template = ENTRY_TEMPLATE):
    if 'previous_answer' not in st.session_state:
        st.session_state.previous_answer = None
    search_results = rrf_search(qdrant_client, query)
    search_results =filter_rrf_results(search_results, DOCUMENTS)
    context = build_context(search_results,entry_template)

    if st.session_state.previous_answer:
        context += f"\n\nPrevious answer:\n{st.session_state.previous_answer}"
    
    prompt = build_prompt(prompt_template,query, context)
    answer = gemini_llm(prompt)

    labels, judge_stats = judge_label(query, context, answer["answer"], OPENAI_API_KEY)
    score = quality_score_from_labels(labels)
    results = {
        "question": query,
        "answer": answer['answer'],
        "quality_score": score,
        "faithfulness": labels.get("faithfulness"),
        "groundedness": labels.get("groundedness"),
        "relevance": labels.get("relevance"),
        "completeness": labels.get("completeness"),
        "coherence": labels.get("coherence"),
        "conciseness": labels.get("conciseness"),
        "tokens_used": answer["tokens_used"],
        "input_tokens": answer["input_tokens"],
        "estimated_cost_usd": answer["estimated_cost_usd"],
        "model_name": answer["model_name"],
        "eval_tokens_used": judge_stats["total_tokens"],
        "eval_input_tokens": judge_stats["prompt_tokens"],
        "eval_estimated_cost_usd": judge_stats["estimated_cost_usd"],

    }

 

    st.session_state.previous_answer = answer
    return results

    

JUDGE_PROMPT_TEMPLATE = """
You are an evaluator. Your task is to classify the quality of the answer provided by a RAG system.
Return ONLY JSON with labels (no extra text). Use one of the allowed labels for each criterion.

Faithfulness: ["NON_FAITHFUL","PARTLY_FAITHFUL","FAITHFUL"]
Groundedness: ["NON_GROUNDED","PARTLY_GROUNDED","GROUNDED"]
Relevance: ["NON_RELEVANT","PARTLY_RELEVANT","RELEVANT"]
Completeness: ["NON_COMPLETE","PARTLY_COMPLETE","COMPLETE"]
Coherence: ["NON_COHERENT","PARTLY_COHERENT","COHERENT"]
Conciseness: ["NON_CONCISE","PARTLY_CONCISE","CONCISE"]

Question: {question}
Context: {context}
Answer: {answer}

Return JSON exactly like:
{{"faithfulness":"...", "groundedness":"...", "relevance":"...", "completeness":"...", "coherence":"...", "conciseness":"..."}}
"""

def judge_label(question, context, answer,OPENAI_API_KEY):
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=question, context=context, answer=answer)
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # LLM-sędzia
        messages=[{"role":"user","content":prompt}],
        temperature=0.0)
    # Collect usage statistics if available
    usage = getattr(resp, "usage", None)
    stats = {
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,

    }

    # Calculate cost (example: $5 per million tokens for GPT-4o-mini, adjust as needed)
    cost = None
    if usage and usage.total_tokens is not None:
        cost = usage.total_tokens / 1_000_000 * 4

    stats["estimated_cost_usd"] = cost

    text = resp.choices[0].message.content.strip()

    text = re.sub(r"```json|```", "", text).strip()
    
    try:
        labels = json.loads(text)
    except json.JSONDecodeError:
        try:
            labels = eval(text)
        except Exception as e:
            print("Failed to parse JSON from model response:", repr(text))
            raise e
    return labels,stats

POSITIVE_MAPPING = {
    "faithfulness": "FAITHFUL",
    "groundedness": "GROUNDED",
    "relevance": "RELEVANT",
    "completeness": "COMPLETE",
    "coherence": "COHERENT",
    "conciseness": "CONCISE"
}

def quality_score_from_labels(labels):
    score = 0
    for crit, pos_label in POSITIVE_MAPPING.items():
        if labels.get(crit) == pos_label:
            score += 1
    return score

