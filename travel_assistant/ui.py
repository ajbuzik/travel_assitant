import uuid
from datetime import datetime
import streamlit as st
from typing import List, Dict, Any
import rag
import persistence

def render_sidebar_stats() -> None:
    st.sidebar.header("📊 Statistics")
    total_questions = len(st.session_state.conversation_history)
    total_feedback = len(st.session_state.feedback_data)
    positive_feedback = len([f for f in st.session_state.feedback_data if f.get('feedback_type') == 'positive'])
    st.sidebar.metric("Total Questions", total_questions)
    st.sidebar.metric("Total Feedback", total_feedback)
    if total_feedback > 0:
        satisfaction_rate = (positive_feedback / total_feedback) * 100
        st.sidebar.metric("Satisfaction Rate", f"{satisfaction_rate:.1f}%")
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear History"):
        st.session_state.conversation_history = []
        st.rerun()

def collect_feedback(question: str, answer: str, conversation_id: str) -> None:
    st.markdown("---")
    st.subheader("📝 Feedback")
    st.write("How was this response?")
    col1, col2 = st.columns([1,1])
    text_feedback_key = f"text_feedback_{conversation_id}"
    with col1:
        thumbs_up = st.button("👍 Good", key=f"thumbs_up_{conversation_id}")
    with col2:
        thumbs_down = st.button("👎 Poor", key=f"thumbs_down_{conversation_id}")
    text_feedback = st.text_area("Additional comments (optional):", key=text_feedback_key,
                                placeholder="Please provide specific feedback on what was good or could be improved...")
    if thumbs_up or thumbs_down:
        feedback_type = "positive" if thumbs_up else "negative"
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_type,
            "text_feedback": text_feedback.strip() if text_feedback else "",
            "conversation_id": conversation_id
        }
        st.session_state.feedback_data.append(feedback)
        persistence.save_feedback(feedback)
        st.success(f"Thank you for your {'positive' if thumbs_up else 'negative'} feedback!")
        st.rerun()

def render_conversation_history() -> None:
    if not st.session_state.conversation_history:
        return
    st.markdown("---")
    st.header("💬 Conversation History")
    for entry in reversed(st.session_state.conversation_history):
        q_preview = (entry['question'][:100] + "...") if len(entry['question']) > 100 else entry['question']
        with st.expander(f"Q: {q_preview}", expanded=True):
            ts = entry.get('timestamp')
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            st.caption(f"Asked on {ts_str}")
            st.markdown("**Question:**")
            st.write(entry['question'])
            st.markdown("**Answer:**")
            st.write(entry.get('answer', ''))
            existing_feedback = [f for f in st.session_state.feedback_data if f.get('conversation_id') == entry['id']]
            if existing_feedback:
                fb = existing_feedback[0]
                icon = "👍" if fb.get('feedback_type') == 'positive' else "👎"
                st.success(f"{icon} Feedback submitted: {fb.get('feedback_type')}")
                if fb.get('text_feedback'):
                    st.info(f"Comment: {fb.get('text_feedback')}")
            else:
                collect_feedback(entry['question'], entry.get('answer', ''), entry['id'])

def qa_page(DOCUMENTS: List[Dict[str, Any]], qdrant_client, OPENAI_API_KEY: str) -> None:
    render_sidebar_stats()
    st.title("🤖 Krakow Travel Assistant - RAG Q&A System")
    st.markdown("Ask any question and get AI-powered answers from Krakow POI database.")

    with st.form("question_form"):
        user_input = st.text_area("Enter your question:", placeholder="Type your question here...", height=100)
        submit_button = st.form_submit_button("🚀 Submit", use_container_width=True)

    if submit_button and user_input and user_input.strip():
        with st.spinner("Generating answer..."):
            try:
                conversation_id = str(uuid.uuid4())
                ts = datetime.now()
                answer = rag.rag(st, user_input.strip(), DOCUMENTS, qdrant_client, OPENAI_API_KEY)
                answer = answer or {}
                answer['id'] = conversation_id
                answer['timestamp'] = ts
                conversation_entry = {
                    "id": conversation_id,
                    "timestamp": ts,
                    "question": user_input.strip(),
                    "answer": answer.get('answer', '')
                }
                st.session_state.conversation_history.append(conversation_entry)
                persistence.save_conversation(answer)
            except Exception as e:
                st.error(f"Error generating answer: {e}")

    render_conversation_history()