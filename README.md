# One-Geo Well-Log Data Analysis System

## 📋 Overview

A full-stack web application for ingesting, storing, visualizing, and performing AI-assisted interpretation on LAS (Log ASCII Standard) well-log data. This system enables geologists and engineers to analyze subsurface well-log measurements through an interactive web interface.

## 🎯 Features

### 1. **File Ingestion & Storage**
- Upload LAS files through a web interface
- Store original files in Amazon S3
- Parse and extract well-log data (depth-indexed measurements)
- Store structured data in PostgreSQL database

### 2. **Interactive Visualization**
- JavaScript-based web UI for visualizing well-log curves
- Plot selected curves against depth
- Support for multiple curve selection
- Depth range filtering
- Interactive controls: zoom, pan, and navigation

### 3. **AI-Assisted Interpretation**
- Analyze selected depth ranges and curves
- AI-powered insights using Hugging Face models
- Generate interpretations based on well-log patterns
- Display results within the application interface

### 4. **Chatbot Interface** (Bonus)
- Conversational interface for data-driven queries
- Ask questions about uploaded well data
- Natural language processing for well-log analysis

## 🏗️ Architecture

### **Backend (Python/FastAPI)**
- RESTful API design with proper separation of concerns
- FastAPI framework for high performance
- PostgreSQL database for structured data storage
- AWS S3 integration for file storage
- LAS file parsing using `lasio` library
- AI integration with Hugging Face models

### **Frontend (React + TypeScript)**
- Modern React application with TypeScript
- Responsive UI design
- Interactive data visualization
- Real-time API communication
- Built with Vite for optimal development experience

### **Database Schema**
- Optimized for depth-indexed measurements
- Supports multiple well logs and curves
- Efficient querying for depth ranges
- PostgreSQL chosen for:
  - ACID compliance
  - Excellent support for time-series/depth-series data
  - Advanced indexing capabilities
  - JSON support for metadata

## 🚀 Deployment

**Live Application:** Deployed on Railway
- Frontend: Served via Railway
- Backend: API hosted on Railway
- Database: PostgreSQL on Railway
- Storage: AWS S3

## 🛠️ Tech Stack

### Backend Dependencies
```
fastapi==0.128.7
uvicorn==0.40.0
starlette==0.52.1
pandas
sqlalchemy==2.0.46
psycopg2-binary==2.9.11
pydantic==2.12.5
numpy==2.2.6
lasio==0.32
huggingface_hub==1.4.1
boto3==1.42.46
python-multipart==0.0.22
python-dotenv==1.2.1
```

### Frontend Dependencies
```
React 18
TypeScript
Vite
React Router
Axios (for API calls)
Plotting library for visualizations
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- AWS Account (for S3)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/BansaLROHanHi/One-Geo_Assignment.git
cd One-Geo_Assignment/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the backend directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/welllog_db
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
HUGGINGFACE_API_KEY=your_hf_api_key
```

5. **Initialize database**
```bash
python -m app.db.init_db
```

6. **Run the backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment**
Create a `.env` file in the frontend directory:
```env
VITE_API_URL=http://localhost:8000
```

4. **Run the development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🐳 Docker Deployment

### Using Docker Compose

```bash
docker-compose up --build
```

This will start:
- Backend API on port 8000
- Frontend on port 5173
- PostgreSQL database

### Individual Docker Builds

**Backend:**
```bash
cd backend
docker build -t welllog-backend .
docker run -p 8000:8000 --env-file .env welllog-backend
```

**Frontend:**
```bash
cd frontend
docker build -t welllog-frontend .
docker run -p 5173:5173 welllog-frontend
```

## 📖 API Documentation

### Key Endpoints

#### File Upload
```
POST /api/v1/upload
Content-Type: multipart/form-data
Body: { file: <LAS file> }
```

#### Get Well Logs
```
GET /api/v1/logs
Response: List of uploaded well logs
```

#### Get Curves
```
GET /api/v1/logs/{log_id}/curves
Response: Available curves for a specific log
```

#### Get Data
```
GET /api/v1/logs/{log_id}/data
Query params: 
  - depth_min: float
  - depth_max: float
  - curves: comma-separated curve names
Response: Filtered well-log data
```

#### AI Interpretation
```
POST /api/v1/interpret
Body: {
  "log_id": "string",
  "depth_min": float,
  "depth_max": float,
  "curves": ["CURVE1", "CURVE2"]
}
Response: AI-generated interpretation
```

#### Chatbot Query
```
POST /api/v1/chat
Body: {
  "log_id": "string",
  "query": "string"
}
Response: Natural language response
```

## 🎨 User Interface

### Main Features
1. **Upload Page**: Drag-and-drop LAS file upload
2. **Log Viewer**: Browse uploaded logs
3. **Visualization Dashboard**: 
   - Select curves to display
   - Set depth ranges
   - Interactive plotting
   - Zoom and pan controls
4. **AI Interpretation Panel**: 
   - Select analysis parameters
   - View AI-generated insights
5. **Chatbot Interface**: 
   - Ask questions about the data
   - Get contextual responses

## 🔒 Security

- Environment variables for sensitive credentials
- API key validation
- CORS configuration
- Input validation and sanitization
- SQL injection prevention via ORM
- File upload restrictions

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📊 Database Design Justification

**PostgreSQL** was chosen for the following reasons:

1. **Structured Data**: Well-log data is inherently structured and relational
2. **ACID Compliance**: Ensures data integrity for critical geological data
3. **Performance**: Excellent for time-series/depth-series queries
4. **Indexing**: Advanced indexing strategies for depth-based queries
5. **JSON Support**: Flexible metadata storage
6. **Scalability**: Proven track record for large datasets
7. **Community**: Strong ecosystem and documentation

### Schema Overview
- `well_logs`: Stores well metadata and S3 references
- `curves`: Stores curve definitions and metadata
- `measurements`: Depth-indexed measurement data
- Proper foreign key relationships and indexes for optimal query performance

## 👥 Contributing

This project is part of an assignment submission. For questions or issues, please contact the repository owner.

## 📝 License

This project is developed as part of an assignment for One-Geo.

## 🎥 Demo Video

A demonstration video showcasing all implemented features is included in the submission.

## 📧 Repository Access

Read access has been granted to:
- shilu143
- mahesh-248
- manish-44
- Grudev100
- crhodes-dev

## ⏰ Submission Details

- **Deadline**: February 15, 2026, 11:59 PM IST
- **Status**: Completed
- **Repository**: [https://github.com/BansaLROHanHi/One-Geo_Assignment](https://github.com/BansaLROHanHi/One-Geo_Assignment)

---

**Built with ❤️ for One-Geo Assignment**
