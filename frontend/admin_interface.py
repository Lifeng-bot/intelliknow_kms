import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="IntelliKnow KMS - Admin Dashboard",
    page_icon="⚙️",
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
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Function to fetch API data
def fetch_api_data(endpoint, max_retries=3, retry_delay=2):
    """
    Fetch data from API endpoint with retry logic.

    Args:
        endpoint: API endpoint to fetch data from
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        JSON response data or None if failed
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch data from {endpoint}. Status code: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                st.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                st.error(f"Connection Error: {str(e)}")
                st.error("Unable to connect to the backend server. Please ensure the backend is running on http://localhost:8000")
                return None
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None

    return None

# Sidebar navigation
with st.sidebar:
    st.title("IntelliKnow KMS Admin")

    page = st.radio(
        "Navigation",
        ["Dashboard", "Knowledge Base", "Intent Configuration", "Analytics"],
        index=["Dashboard", "Knowledge Base", "Intent Configuration", "Analytics"].index(st.session_state.current_page)
    )

    st.session_state.current_page = page

# Main content based on selected page
if st.session_state.current_page == "Dashboard":
    st.markdown('<div class="main-header">📊 Dashboard</div>', unsafe_allow_html=True)

    # Fetch metrics
    metrics = fetch_api_data("/api/analytics/metrics")

    if metrics:
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{metrics["total_documents"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Total Documents</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{metrics["total_queries"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Total Queries</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{metrics["total_intents"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Intent Spaces</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Display query counts by intent
        st.subheader("Query Distribution by Intent")
        if metrics["intent_query_counts"]:
            intent_df = pd.DataFrame(
                list(metrics["intent_query_counts"].items()),
                columns=["Intent", "Query Count"]
            )
            st.bar_chart(intent_df.set_index("Intent"))

        # Display recent queries
        st.subheader("Recent Queries")
        if metrics["recent_queries"]:
            recent_queries_df = pd.DataFrame(metrics["recent_queries"])
            recent_queries_df["timestamp"] = pd.to_datetime(recent_queries_df["timestamp"])
            st.dataframe(recent_queries_df[["query", "intent", "confidence", "timestamp"]])

elif st.session_state.current_page == "Knowledge Base":
    st.markdown('<div class="main-header">📚 Knowledge Base Management</div>', unsafe_allow_html=True)

    # Tabs for different KB operations
    kb_tab1, kb_tab2, kb_tab3 = st.tabs(["Upload Document", "View Documents", "Manage Documents"])

    with kb_tab1:
        st.subheader("Upload Document")

        # Intent selection
        intents = fetch_api_data("/api/intents")
        intent_options = [intent["name"] for intent in intents] if intents else []

        selected_intent = st.selectbox("Select Intent Space", ["None"] + intent_options)

        # File upload
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["pdf", "docx"],
            help="Upload PDF or DOCX files to add to the knowledge base"
        )

        if uploaded_file and st.button("Upload"):
            with st.spinner("Uploading and processing document..."):
                # Prepare files and data for upload
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                # Only include intent in data if it's not "None"
                data = {}
                if selected_intent != "None":
                    data["intent"] = selected_intent

                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/kb/upload",
                        files=files,
                        data=data,
                        timeout=60
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Document uploaded successfully! ID: {result['document_id']}")
                        st.info(f"Chunks processed: {result['chunks_count']}")
                    else:
                        st.error(f"Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"Upload error: {str(e)}")

    with kb_tab2:
        st.subheader("View Documents")

        # Intent filter
        intents = fetch_api_data("/api/intents")
        intent_options = [intent["name"] for intent in intents] if intents else []

        selected_intent = st.selectbox("Filter by Intent", ["All"] + intent_options)

        # Fetch documents
        intent_param = None if selected_intent == "All" else selected_intent
        documents = fetch_api_data(f"/api/kb/documents?intent={intent_param}" if intent_param else "/api/kb/documents")

        if documents:
            documents_df = pd.DataFrame(documents)
            documents_df["uploaded_at"] = pd.to_datetime(documents_df["uploaded_at"])
            st.dataframe(documents_df[["id", "filename", "file_type", "intent", "uploaded_at", "processed"]])
        else:
            st.info("No documents found in the knowledge base.")

    with kb_tab3:
        st.subheader("Manage Documents")

        # Document selection
        documents = fetch_api_data("/api/kb/documents")

        if documents:
            document_options = {f"{doc['id']} - {doc['filename']}": doc['id'] for doc in documents}
            selected_document = st.selectbox("Select Document", list(document_options.keys()))

            if selected_document:
                document_id = document_options[selected_document]

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("View Details"):
                        document_details = fetch_api_data(f"/api/kb/documents/{document_id}")
                        if document_details:
                            st.json(document_details)

                with col2:
                    if st.button("Reprocess"):
                        with st.spinner("Reprocessing document..."):
                            response = requests.post(
                                f"{API_BASE_URL}/api/kb/documents/{document_id}/reprocess",
                                timeout=60
                            )

                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"Document reprocessed successfully! Chunks: {result['chunks_count']}")
                            else:
                                st.error(f"Reprocessing failed: {response.text}")

                if st.button("Delete Document", type="primary"):
                    response = requests.delete(f"{API_BASE_URL}/api/kb/documents/{document_id}")

                    if response.status_code == 200:
                        st.success("Document deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Deletion failed: {response.text}")
        else:
            st.info("No documents found in the knowledge base.")

elif st.session_state.current_page == "Intent Configuration":
    st.markdown('<div class="main-header">🎯 Intent Configuration</div>', unsafe_allow_html=True)

    # Tabs for different intent operations
    intent_tab1, intent_tab2, intent_tab3 = st.tabs(["View Intents", "Create Intent", "Manage Intents"])

    with intent_tab1:
        st.subheader("View Intents")

        intents = fetch_api_data("/api/intents")

        if intents:
            intents_df = pd.DataFrame(intents)
            intents_df["created_at"] = pd.to_datetime(intents_df["created_at"])
            intents_df["updated_at"] = pd.to_datetime(intents_df["updated_at"])
            st.dataframe(intents_df[["id", "name", "description", "confidence_threshold", "created_at", "updated_at"]])
        else:
            st.info("No intents found.")

    with intent_tab2:
        st.subheader("Create New Intent")

        intent_name = st.text_input("Intent Name")
        intent_description = st.text_area("Description")
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Minimum confidence level for queries to be classified to this intent"
        )

        if st.button("Create Intent"):
            if not intent_name:
                st.error("Intent name is required")
            else:
                intent_data = {
                    "name": intent_name,
                    "description": intent_description,
                    "confidence_threshold": confidence_threshold
                }

                response = requests.post(
                    f"{API_BASE_URL}/api/intents",
                    json=intent_data
                )

                if response.status_code == 200:
                    st.success("Intent created successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to create intent: {response.text}")

    with intent_tab3:
        st.subheader("Manage Intents")

        intents = fetch_api_data("/api/intents")

        if intents:
            intent_options = {f"{intent['id']} - {intent['name']}": intent['id'] for intent in intents}
            selected_intent = st.selectbox("Select Intent", list(intent_options.keys()))

            if selected_intent:
                intent_id = intent_options[selected_intent]
                intent_details = next((intent for intent in intents if intent["id"] == intent_id), None)

                if intent_details:
                    st.write("Current Intent Details:")
                    st.json(intent_details)

                    st.write("Update Intent:")
                    updated_name = st.text_input("Intent Name", value=intent_details["name"])
                    updated_description = st.text_area("Description", value=intent_details["description"] or "")
                    updated_threshold = st.slider(
                        "Confidence Threshold",
                        min_value=0.0,
                        max_value=1.0,
                        value=intent_details["confidence_threshold"],
                        step=0.05
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Update Intent"):
                            intent_data = {
                                "name": updated_name,
                                "description": updated_description,
                                "confidence_threshold": updated_threshold
                            }

                            response = requests.put(
                                f"{API_BASE_URL}/api/intents/{intent_id}",
                                json=intent_data
                            )

                            if response.status_code == 200:
                                st.success("Intent updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update intent: {response.text}")

                    with col2:
                        if st.button("Delete Intent"):
                            response = requests.delete(f"{API_BASE_URL}/api/intents/{intent_id}")

                            if response.status_code == 200:
                                st.success("Intent deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete intent: {response.text}")
        else:
            st.info("No intents found.")

elif st.session_state.current_page == "Analytics":
    st.markdown('<div class="main-header">📈 Analytics</div>', unsafe_allow_html=True)

    # Tabs for different analytics views
    analytics_tab1, analytics_tab2 = st.tabs(["Query History", "Export Data"])

    with analytics_tab1:
        st.subheader("Query History")

        # Fetch query history
        limit = st.slider("Number of queries to display", 10, 500, 100)
        offset = st.number_input("Offset", min_value=0, value=0)

        query_history = fetch_api_data(f"/api/analytics/history?limit={limit}&offset={offset}")

        if query_history:
            query_history_df = pd.DataFrame(query_history)
            query_history_df["timestamp"] = pd.to_datetime(query_history_df["timestamp"])
            st.dataframe(query_history_df[["id", "query", "intent", "confidence", "timestamp"]])
        else:
            st.info("No query history found.")

    with analytics_tab2:
        st.subheader("Export Data")

        export_format = st.selectbox("Export Format", ["CSV", "JSON"])

        if st.button("Export Query History"):
            query_history = fetch_api_data("/api/analytics/history?limit=1000")

            if query_history:
                if export_format == "CSV":
                    query_history_df = pd.DataFrame(query_history)
                    query_history_df["timestamp"] = pd.to_datetime(query_history_df["timestamp"])
                    csv = query_history_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    import json
                    json_data = json.dumps(query_history, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.info("No query history to export.")
