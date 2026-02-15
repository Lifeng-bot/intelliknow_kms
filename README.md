# IntelliKnow KMS - Gen AI-Powered Knowledge Management System

## Overview
IntelliKnow KMS is a lightweight, AI-powered knowledge management system with intelligent query orchestration, document-driven knowledge base, and modern frontend interfaces.

## Features
- **Knowledge Retrieval**: AI-powered responses with citations from the knowledge base
- **User Interface**: Clean chat interface for querying the knowledge base
- **Admin Dashboard**: Comprehensive admin panel with:
  - Dashboard with analytics
  - Knowledge Base management with document upload
  - Intent configuration
  - Analytics and history tracking
- **Query Orchestration**: AI-powered intent classification with configurable confidence thresholds
- **Document Processing**: Support for PDF and DOCX documents with AI parsing
- **Semantic Search**: FAISS-based vector search for accurate document retrieval
- **Analytics**: Query logging, metrics tracking, and exportable data

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Streamlit
- **Database**: SQLite
- **Vector Search**: FAISS
- **Document Processing**: PyPDF2, python-docx
- **AI/ML**: DeepSeek models, LangChain, sentence-transformers
- **Async Processing**: aiofiles, aiohttp

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- DeepSeek API key

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelliknow-kms.git
cd intelliknow-kms
```

2. Create a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the root directory:
```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATABASE_URL=sqlite:///./intelliknow.db
FAISS_INDEX_PATH=./data/faiss_index
```

5. Run the application:
```bash
# Start all services at once using the start.py script
python start.py
```

The start.py script will:
- Check if all dependencies are installed
- Verify environment variables are set
- Initialize the database
- Start the backend server on http://localhost:8000
- Start the user interface on http://localhost:8501
- Start the admin interface on http://localhost:8502

All logs will be saved to the `logs` directory with timestamps.

## Usage

### User Interface
1. Navigate to the user interface URL (typically http://localhost:8501)
2. Type your question in the chat input
3. Receive AI-generated responses with citations from the knowledge base

### Admin Dashboard
1. Navigate to the admin interface URL (typically http://localhost:8502)
2. Dashboard: View system metrics and recent activity
3. KB Management: Upload, manage, and organize documents
4. Intent Configuration: Configure intent spaces and classification rules
5. Analytics: View query history, metrics, and export data

### Stopping the Application
To stop all services, press `Ctrl+C` in the terminal where start.py is running. This will gracefully shutdown all services (backend, user interface, and admin interface).

## API Endpoints

### Knowledge Base
- `POST /api/kb/upload` - Upload a document to the knowledge base
- `GET /api/kb/documents` - List all documents in the knowledge base
- `GET /api/kb/documents/{document_id}` - Get details of a specific document
- `DELETE /api/kb/documents/{document_id}` - Delete a document from the knowledge base
- `POST /api/kb/documents/{document_id}/reprocess` - Re-process a document in the knowledge base

### Query
- `POST /api/query` - Submit a query and get a response
- `GET /api/query/history` - Get query history

### Intent
- `GET /api/intents` - List all intent spaces
- `POST /api/intents` - Create a new intent space
- `PUT /api/intents/{intent_id}` - Update an intent space
- `DELETE /api/intents/{intent_id}` - Delete an intent space

### Analytics
- `GET /api/analytics/metrics` - Get system metrics
- `GET /api/analytics/history` - Get query history for analytics
