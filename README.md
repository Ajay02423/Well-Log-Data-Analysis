# One-Geo Well-Log Data Analysis System

## 📋 Overview

A full-stack web application for ingesting, storing, visualizing, and performing AI-assisted interpretation on LAS (Log ASCII Standard) well-log data. This system enables users to upload geological data, visualize various curves against depth, and get AI-powered insights using large language models.

## 🎯 Features

- **LAS File Ingestion**: Upload and process `.las` files with background processing.
- **Dual Storage**: Original files in Amazon S3 and structured data in PostgreSQL.
- **Interactive Visualization**: Multi-curve plotting with depth range selection using Plotly.
- **AI Interpretation**: Automated geological insights using Hugging Face/OpenAI models.
- **AI Chatbot**: Conversational interface to ask data-driven questions about the well logs.
- **Real-time Progress**: Background task tracking for data ingestion.

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React (v19) + TypeScript + Vite
- **Database**: PostgreSQL (via SQLAlchemy ORM)
- **Cloud Storage**: Amazon S3
- **Deployment**: Railway (Live Environment)

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

## 🚀 Setup & Installation

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
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Environment Variables (`backend/.env`):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/well_db
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket
HF_API_TOKEN=your_token
OPENAI_API_KEY=your_key  # Optional
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
```env
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

## 📖 API Reference

- **List Wells**: `GET /api/v1/wells`
- **Well Curves**: `GET /api/v1/wells/{id}/curves`
- **Depth Range Data**: `POST /api/v1/query`
- **Upload Presign**: `POST /api/v1/presign-upload`
- **Confirm Upload**: `POST /api/v1/confirm-upload`
- **AI Interpretation**: `POST /api/v1/interpret`
- **Chatbot**: `POST /api/v1/chat`

---
**Built for the One-Geo Assignment**
