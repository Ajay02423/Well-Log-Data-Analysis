# One-Geo Well-Log Data Analysis System

##  Overview

A full-stack web application for ingesting, storing, visualizing, and performing AI-assisted interpretation on LAS (Log ASCII Standard) well-log data. This system enables users to upload geological data, visualize various curves against depth, and get AI-powered insights using large language models.

##  Features

- **LAS File Ingestion**: Upload and process `.las` files with background processing.
- **Dual Storage**: Original files in Amazon S3 and structured data in PostgreSQL.
- **Interactive Visualization**: Multi-curve plotting with depth range selection using Plotly.
- **AI Interpretation**: Automated geological insights using Hugging Face/OpenAI models.
- **AI Chatbot**: Conversational interface to ask data-driven questions about the well logs.
- **Real-time Progress**: Background task tracking for data ingestion.

##  Approach & Design Decisions

### 1. Architecture
*   **Separation of Concerns**: The system follows a clear client-server architecture. The **FastAPI** backend handles data processing, storage orchestration, and AI integration, while the **React** frontend provides a responsive user interface.
*   **API-First Design**: Communication happens via a well-defined REST API. This ensures that the frontend never interacts directly with the database or S3 credentials, maintaining a secure boundary.
*   **Security**: Sensitive AWS and AI credentials are kept strictly on the server-side within the backend's environment variables. The frontend uses **S3 Presigned URLs** to upload files directly to S3 without exposing secret keys.

### 2. File Ingestion & Storage Strategy
*   **Two-Phase Upload**: 
    1.  Frontend requests a presigned URL from the backend.
    2.  Frontend uploads the `.las` file directly to the **Amazon S3** bucket.
    3.  Backend is notified to start processing.
*   **Processing Pipeline**: The backend uses the `lasio` library to parse the Log ASCII Standard file. 
*   **Database Choice: PostgreSQL**: 
    *   **Justification**: PostgreSQL was chosen for its reliability, support for structured relational data (well metadata, curve definitions), and its ability to efficiently store and query large time-series/depth-series data using standard SQL. It allows for complex queries when filtering by depth ranges and curves.
*   **Storage Strategy**: 
    *   **Original Files**: Kept in S3 for archival and re-processing.
    *   **Parsed Data**: Curve data (e.g., GR, NPHI, RHOB) is stored in a structured format in PostgreSQL on AWS RDS, indexed by `well_id` and `depth` to enable high-performance retrieval for visualization.

### 3. Visualization Approach
*   **Interactive Engine**: Uses **Plotly.js** due to its superior support for scientific charting, built-in zoom/pan capabilities, and ability to handle large datasets.
*   **Dynamic Loading**: Instead of loading the entire log at once, the frontend requests specific curves and depth ranges via the `/api/v1/query` endpoint, ensuring the UI remains performant even for deep wells.

### 4. AI-Assisted Interpretation
*   **Technique**: Large Language Models (LLMs) from **Hugging Face** are used to perform geological analysis.
*   **Process**: 
    1.  The user selects a depth range and curves (e.g., Gamma Ray and Resistivity).
    2.  The backend extracts the statistical summary and raw data for that range.
    3.  A prompt is constructed with the log data and sent to the AI model.
    4.  **Insights**: The AI provides lithology interpretation, identifies potential pay zones, and highlights anomalies in the well-log trends.

### 5. Chatbot Interface
*   **Conversational Data Analysis**: A dedicated chatbot allows users to ask natural language questions (e.g., \"What is the average Gamma Ray between 1000ft and 1200ft?\"). It combines the power of LLMs with structured data queries to provide real-time answers based on the uploaded well data.

##  Architecture

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React (v19) + TypeScript + Vite
- **Database**: PostgreSQL on AWS(RDS)
- **Cloud Storage**: Amazon S3
- **LLM**: Qwen2.5-7B-Instruct
- **Deployment**: Railway (Backend), Vercel (Frontend)

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, high-performance web framework.
- **SQLAlchemy**: Database ORM for PostgreSQL.
- **lasio**: Specialized library for LAS file parsing.
- **Boto3**: AWS SDK for S3 integration.
- **Pydantic**: Data validation and settings management.

### Frontend
- **React 19**: Modern UI library.
- **TypeScript**: Static typing for robust development.
- **Plotly.js**: High-performance interactive charting.
- **Axios**: HTTP client for API communication.

##  Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional for containerized setup)
- AWS Account (S3 access)
- Hugging Face / OpenAI API Key

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

**Environment Variables (`backend/.env`):**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/well_db
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-west-1
S3_BUCKET_NAME=your_bucket
HF_API_TOKEN=your_token
```

**Run Server:**
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

**Environment Variables (`frontend/.env`):**
```bash
VITE_API_URL=http://localhost:8000
```

**Run Dev Server:**
```bash
npm run dev
```

### 3. Docker Setup (Alternative)
```bash
docker-compose up --build
```

##  API Reference

- **List Wells**: `GET /api/v1/wells`
- **Well Curves**: `GET /api/v1/wells/{id}/curves`
- **Depth Range Data**: `POST /api/v1/query`
- **Upload Presign**: `POST /api/v1/presign-upload`
- **Confirm Upload**: `POST /api/v1/confirm-upload`
- **AI Interpretation**: `POST /api/v1/interpret`
- **Chatbot**: `POST /api/v1/chat`

---
