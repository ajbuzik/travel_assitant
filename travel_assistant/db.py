import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
load_dotenv()
import json
import datetime
from typing import Any, Dict, List, Optional

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "travel_assistant"),
        user=os.getenv("POSTGRES_USER", "your_username"),
        password=os.getenv("POSTGRES_PASSWORD", "your_password"),
    )

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")
            cur.execute("DROP TABLE IF EXISTS conversations")

            cur.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL ,
                    answer TEXT NOT NULL ,
                    quality_score FLOAT NOT NULL ,
                    faithfulness TEXT NOT NULL,
                    groundedness TEXT NOT NULL,
                    relevance TEXT NOT NULL,
                    completeness TEXT NOT NULL,
                    coherence TEXT NOT NULL,
                    conciseness TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    estimated_cost_usd FLOAT NOT NULL,
                    model_name TEXT NOT NULL,
                    eval_input_tokens INTEGER NOT NULL,
                    eval_tokens_used INTEGER NOT NULL,  
                    eval_estimated_cost_usd FLOAT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                     )   
            """)
            cur.execute("""
                CREATE TABLE feedback (
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    feedback_type TEXT NOT NULL,
                    text_feedback TEXT NOT NULL,
                    conversation_id TEXT PRIMARY KEY
                )
            """)
        conn.commit()
    finally:
        conn.close()


def save_conversation(answear):

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations 
                (id,
question,
answer,
quality_score,
faithfulness,
groundedness,
relevance,
completeness,
coherence,
conciseness,
tokens_used,
input_tokens,
estimated_cost_usd,
model_name,
eval_input_tokens,
eval_tokens_used,
eval_estimated_cost_usd,
timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s)
                """,
                (
                    answear['id'],
                    answear['question'],
                    answear['answer'],
                    answear['quality_score'],
                    answear['faithfulness'],
                    answear['groundedness'],
                    answear['relevance'],
                    answear['completeness'],
                    answear['coherence'],
                    answear['conciseness'],
                    answear['tokens_used'],
                    answear['input_tokens'],
                    answear['estimated_cost_usd'],
                    answear['model_name'],
                    answear['eval_input_tokens'],
                    answear['eval_tokens_used'],
                    answear['eval_estimated_cost_usd'],
                    answear['timestamp']
                ),
            )
        conn.commit()
    finally:
        conn.close()


def save_feedback( feedback):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (timestamp, feedback_type, text_feedback, conversation_id) VALUES (%s, %s, %s, %s)",
                (feedback['timestamp'], feedback['feedback_type'], feedback['text_feedback'], feedback['conversation_id']),
            )
        conn.commit()
    finally:
        conn.close()




def get_conversation_data():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM conversations ORDER BY timestamp DESC")
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def get_feedback_data():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()

def _parse_timestamp(value: Any) -> datetime.datetime:
    """Robust timestamp parser: accepts ISO strings, naive/datetime, unix epoch."""
    if value is None:
        return datetime.datetime.now(datetime.timezone.utc)
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(value, datetime.timezone.utc)
    if isinstance(value, str):
        # Try several common formats, fallback to now UTC
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                # datetime.fromisoformat handles many ISO cases
                if fmt.startswith("%Y-%m-%dT"):
                    return datetime.datetime.fromisoformat(value)
                return datetime.datetime.strptime(value, fmt)
            except Exception:
                continue
    # final fallback
    return datetime.datetime.now(datetime.timezone.utc)

def import_conversations_from_file(filename: str = "answer_data.json") -> Dict[str, int]:
    """
    Load conversation records from travel_assistant/data/<filename> into the conversations table.
    Missing fields are filled with sensible defaults. Returns a dict with counts.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", filename)
    if not os.path.exists(data_path):
        return {"inserted": 0, "skipped": 0, "errors": 0}

    with open(data_path, "r", encoding="utf-8") as f:
        try:
            items = json.load(f)
        except Exception:
            return {"inserted": 0, "skipped": 0, "errors": 1}

    inserted = 0
    skipped = 0
    errors = 0

    insert_sql = """
        INSERT INTO conversations
        (id, question, answer, quality_score, faithfulness, groundedness, relevance, completeness,
         coherence, conciseness, tokens_used, input_tokens, estimated_cost_usd, model_name,
         eval_input_tokens, eval_tokens_used, eval_estimated_cost_usd, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for rec in items:
                try:
                    ts = _parse_timestamp(rec.get("timestamp"))
                    vals = (
                        rec.get("id"),
                        rec.get("question", ""),
                        rec.get("answer", ""),
                        float(rec.get("quality_score", 0.0) or 0.0),
                        rec.get("faithfulness", ""),
                        rec.get("groundedness", ""),
                        rec.get("relevance", ""),
                        rec.get("completeness", ""),
                        rec.get("coherence", ""),
                        rec.get("conciseness", ""),
                        int(rec.get("tokens_used", 0) or 0),
                        int(rec.get("input_tokens", 0) or 0),
                        float(rec.get("estimated_cost_usd", 0.0) or 0.0),
                        rec.get("model_name", ""),
                        int(rec.get("eval_input_tokens", 0) or 0),
                        int(rec.get("eval_tokens_used", 0) or 0),
                        float(rec.get("eval_estimated_cost_usd", 0.0) or 0.0),
                        ts,
                    )
                    cur.execute(insert_sql, vals)
                    if cur.rowcount and cur.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                except Exception:
                    errors += 1
        conn.commit()
    finally:
        conn.close()

    return {"inserted": inserted, "skipped": skipped, "errors": errors}

def import_feedback_from_file(filename: str = "feedback_data.json") -> Dict[str, int]:
    """
    Load feedback records from travel_assistant/data/<filename> into the feedback table.
    Returns counts.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", filename)
    if not os.path.exists(data_path):
        return {"inserted": 0, "skipped": 0, "errors": 0}

    with open(data_path, "r", encoding="utf-8") as f:
        try:
            items = json.load(f)
        except Exception:
            return {"inserted": 0, "skipped": 0, "errors": 1}

    inserted = 0
    skipped = 0
    errors = 0

    insert_sql = """
        INSERT INTO feedback (timestamp, feedback_type, text_feedback, conversation_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (conversation_id) DO NOTHING
    """

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for rec in items:
                try:
                    ts = _parse_timestamp(rec.get("timestamp"))
                    vals = (
                        ts,
                        rec.get("feedback_type", ""),
                        rec.get("text_feedback", ""),
                        rec.get("conversation_id"),
                    )
                    cur.execute(insert_sql, vals)
                    if cur.rowcount and cur.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                except Exception:
                    errors += 1
        conn.commit()
    finally:
        conn.close()

    return {"inserted": inserted, "skipped": skipped, "errors": errors}