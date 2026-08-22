# VaaniRAG

A hackathon-ready Voice-Enabled Retrieval-Augmented Generation system.

## Setup

1. Configure environment variables in `.env` based on `.env.example`.
2. Install frontend dependencies: `cd frontend && npm install`
3. Install backend dependencies: `cd backend && pip install -r requirements.txt`
4. Run data ingestion: `cd scripts && python ingest_data.py`
5. Run index building: `cd scripts && python build_indexes.py`

## Running Locally

Using Docker:
```
docker-compose up --build
```

Or manually:
Backend: `cd backend && uvicorn app.main:app --reload`
Frontend: `cd frontend && npm run dev`
