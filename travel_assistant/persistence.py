import os
import json
from typing import Any, Dict
import streamlit as st
import datetime
import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def _save_json_list_item(filename: str, item: Dict[str, Any]) -> bool:
    path = os.path.join(DATA_DIR, filename)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(item)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, default=str, ensure_ascii=False)
        return True
    except Exception as e:
        # non-fatal: log to Streamlit and return False
        try:
            st.error(f"Error saving {filename}: {e}")
        except Exception:
            pass
        return False

def save_feedback(feedback: Dict[str, Any]) -> bool:
    """Persist feedback to DB (if available) and to disk."""
    try:
        db.save_feedback(feedback)
    except Exception:
        # do not fail the UI if DB is unavailable
        pass
    return _save_json_list_item("feedback_data.json", feedback)

def save_conversation(answer: Dict[str, Any]) -> bool:
    """Persist conversation/answer to DB and disk."""
    try:
        db.save_conversation(answer)
    except Exception:
        pass
    return _save_json_list_item("answer_data.json", answer)