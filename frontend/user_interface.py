import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="IntelliKnow KMS - User Interface",
    page_icon="🧠",
    layout="wide"
)

# API base URL
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .citation {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .high-confidence {
        background-color: #d4edda;
        color: #155724;
    }
    .medium-confidence {
        background-color: #fff3cd;
        color: #856404;
    }
    .low-confidence {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header
st.markdown('<div class="main-header">🧠 IntelliKnow KMS</div>', unsafe_allow_html=True)
st.markdown("Ask questions and get AI-powered responses with citations from the knowledge base.")

# Function to process query
def process_query(query_text):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={"query": query_text},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API Error: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "error": f"Connection Error: {str(e)}"
        }

# Chat interface
chat_container = st.container()

# Display chat history
with chat_container:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            # Assistant message
            response_content = message["content"]

            # Check if response is an error
            if "error" in response_content:
                st.markdown(f'<div class="chat-message assistant-message"><strong>AI Assistant:</strong> {response_content["error"]}</div>', unsafe_allow_html=True)
            else:
                # Display response
                st.markdown(f'<div class="chat-message assistant-message"><strong>AI Assistant:</strong> {response_content["response"]}</div>', unsafe_allow_html=True)

                # Display confidence
                confidence = response_content.get("confidence", 0.0)
                confidence_class = "high-confidence" if confidence >= 0.7 else "medium-confidence" if confidence >= 0.4 else "low-confidence"
                st.markdown(f'<span class="confidence-badge {confidence_class}">Normalized Confidence: {confidence:.2f}</span>', unsafe_allow_html=True)

                # Display intent if available
                if "intent" in response_content and response_content["intent"]:
                    st.markdown(f'<small>Intent: {response_content["intent"]} (Intent Confidence: {response_content.get("intent_confidence", 0.0):.2f})</small>', unsafe_allow_html=True)

                # Display citations if available
                if "citations" in response_content and response_content["citations"]:
                    st.markdown("#### Citations:")
                    for citation in response_content["citations"]:
                        st.markdown(f'<div class="citation"><strong>{citation["title"]}</strong><br>{citation["snippet"]}</div>', unsafe_allow_html=True)

# User input
user_input = st.text_input("Your question:", key="user_input")

# Submit button
if st.button("Send"):
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        # Process query
        with st.spinner("Thinking..."):
            response = process_query(user_input)

        # Add assistant response to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })

        # Rerun to update the chat display
        st.rerun()

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()

# Sidebar with additional options
with st.sidebar:
    st.header("Options")

    # Display system status
    st.subheader("System Status")
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.json()
            st.metric("Total Documents", metrics["total_documents"])
            st.metric("Total Queries", metrics["total_queries"])
            st.metric("Intents Available", metrics["total_intents"])
        else:
            st.error("Failed to fetch system status")
    except:
        st.error("Failed to connect to API server")

    # Display recent queries
    st.subheader("Recent Queries")
    try:
        response = requests.get(f"{API_BASE_URL}/api/query/history?limit=5", timeout=10)
        if response.status_code == 200:
            queries = response.json()
            for query in queries:
                st.markdown(f"- {query['query'][:50]}...")
        else:
            st.error("Failed to fetch recent queries")
    except:
        st.error("Failed to connect to API server")

    # About section
    st.subheader("About")
    st.markdown("""
    IntelliKnow KMS is a Gen AI-powered knowledge management system that helps you find answers from your organization's knowledge base.

    Features:
    - AI-powered responses with citations
    - Intent-based query routing
    - Semantic search across documents
    """)
