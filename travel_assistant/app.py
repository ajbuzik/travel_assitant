import streamlit as st
import json
import datetime
from typing import Dict, Any
import os
import rag   
import ingest
# Configure page
from qdrant_client import QdrantClient
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


st.set_page_config(
    page_title="Krakow Travel Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

def save_feedback_to_file(feedback_data: Dict[str, Any], filename: str = "feedback_data.json"):
    """Save feedback data to a JSON file"""
    try:
        # Load existing data
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Append new feedback
        existing_data.append(feedback_data)
        
        # Save back to file
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=2, default=str)
        
        return True
    except Exception as e:
        st.error(f"Error saving feedback: {str(e)}")
        return False

def collect_feedback(question: str, answer: str, conversation_id: int):
    """Display feedback collection interface"""
    st.markdown("---")
    st.subheader("📝 Feedback")
    st.write("How was this response?")
    
    col1, col2 = st.columns(2)
    
    feedback_key = f"feedback_{conversation_id}"
    text_feedback_key = f"text_feedback_{conversation_id}"
    
    with col1:
        thumbs_up = st.button("👍 Good", key=f"thumbs_up_{conversation_id}")
    with col2:
        thumbs_down = st.button("👎 Poor", key=f"thumbs_down_{conversation_id}")
    
    # Text feedback
    text_feedback = st.text_area(
        "Additional comments (optional):",
        key=text_feedback_key,
        placeholder="Please provide specific feedback on what was good or could be improved..."
    )
    
    # Process feedback
    if thumbs_up or thumbs_down:
        feedback_type = "positive" if thumbs_up else "negative"
        
        feedback_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "feedback_type": feedback_type,
            "text_feedback": text_feedback.strip() if text_feedback else "",
            "conversation_id": conversation_id
        }
        
        # Save to session state
        st.session_state.feedback_data.append(feedback_data)
        
        # Save to file
        if save_feedback_to_file(feedback_data):
            st.success(f"Thank you for your {'positive' if thumbs_up else 'negative'} feedback!")
        
        # Optional: Remove the feedback buttons after submission
        st.rerun()

def main():
    qdrant_client = QdrantClient("http://localhost:6333")

    if 'DOCUMENTS' not in st.session_state or 'qdrant_client' not in st.session_state:
        DOCUMENTS, qdrant_client = ingest.load_data(qdrant_client)
        st.session_state.DOCUMENTS = DOCUMENTS
        st.session_state.qdrant_client = qdrant_client
    else:
        DOCUMENTS = st.session_state.DOCUMENTS
        qdrant_client = st.session_state.qdrant_client

    st.title("🤖 Krakow Travel Assistant - RAG Q&A System")
    st.markdown("Ask any question and get AI-powered answers from Krakow POI database.")
    
    # Sidebar for settings and stats
    with st.sidebar:
        st.header("📊 Statistics")
        total_questions = len(st.session_state.conversation_history)
        total_feedback = len(st.session_state.feedback_data)
        positive_feedback = len([f for f in st.session_state.feedback_data if f['feedback_type'] == 'positive'])
        
        st.metric("Total Questions", total_questions)
        st.metric("Total Feedback", total_feedback)
        if total_feedback > 0:
            satisfaction_rate = (positive_feedback / total_feedback) * 100
            st.metric("Satisfaction Rate", f"{satisfaction_rate:.1f}%")
        
        st.markdown("---")
        if st.button("Clear History"):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Main input area
    with st.form("question_form"):
        user_input = st.text_area(
            "Enter your question:",
            placeholder="Type your question here...",
            height=100
        )
        submit_button = st.form_submit_button("🚀 Submit", use_container_width=True)
    
    # Process question when submitted
    if submit_button and user_input.strip():
        with st.spinner("Generating answer..."):
            # Get answer from RAG function
            try:
                answer = rag.rag(st,user_input.strip(), DOCUMENTS, qdrant_client)
                
                # Add to conversation history
                conversation_entry = {
                    "id": len(st.session_state.conversation_history),
                    "timestamp": datetime.datetime.now(),
                    "question": user_input.strip(),
                    "answer": answer
                }
                st.session_state.conversation_history.append(conversation_entry)
                
            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")
                answer = None
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.header("💬 Conversation History")
        
        # Display conversations in reverse order (most recent first)
        for entry in reversed(st.session_state.conversation_history):
            with st.expander(f"Q: {entry['question'][:100]}..." if len(entry['question']) > 100 else f"Q: {entry['question']}", expanded=True):
                
                # Display timestamp
                st.caption(f"Asked on {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Display question
                st.markdown("**Question:**")
                st.write(entry['question'])
                
                # Display answer
                st.markdown("**Answer:**")
                st.write(entry['answer'])
                
                # Check if feedback already exists for this conversation
                existing_feedback = [f for f in st.session_state.feedback_data if f['conversation_id'] == entry['id']]
                
                if existing_feedback:
                    # Show existing feedback
                    feedback = existing_feedback[0]
                    feedback_icon = "👍" if feedback['feedback_type'] == 'positive' else "👎"
                    st.success(f"{feedback_icon} Feedback submitted: {feedback['feedback_type']}")
                    if feedback['text_feedback']:
                        st.info(f"Comment: {feedback['text_feedback']}")
                else:
                    # Show feedback collection interface
                    collect_feedback(entry['question'], entry['answer'], entry['id'])
    

if __name__ == "__main__":
    main()