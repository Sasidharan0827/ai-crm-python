# Aivoa Backend

FastAPI backend for an AI-assisted CRM module focused on HCP (healthcare professional) workflows. The service exposes CRUD-style API endpoints for HCPs and interactions, and includes an agent endpoint backed by Groq via LangChain/LangGraph.

## Features

- FastAPI service with CORS support
- PostgreSQL via SQLAlchemy and Psycopg
- Automatic schema creation on startup
- Seeded sample HCP and interaction data for local development
- Agent tools for:
  - listing HCPs
  - fetching HCP snapshots
  - logging interactions
  - editing interactions
  - recommending next best actions
  - drafting follow-up notes

## Requirements

- Python 3.10+
- PostgreSQL

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root. You can start from `.env.example`.

```env
DATABASE_URL=postgresql+psycopg://postgres:admin123@localhost:5432/aivoa_crm
GROQ_API_KEY=actual_key_here
GROQ_MODEL=llama-3.1-8b-instant
FRONTEND_ORIGIN=http://localhost:5173
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Startup Behavior

On startup, the application:

- creates database tables if they do not already exist
- seeds sample HCP and interaction data if the database is empty
- validates the configured PostgreSQL connection

If the database connection fails, the app raises a startup error that points to `DATABASE_URL`.

## API Endpoints

### Health

- `GET /health`

Returns service health plus whether the Groq API key is configured.

### HCPs

- `GET /api/hcps`
- `GET /api/hcps/{hcp_id}`

### Interactions

- `GET /api/interactions`
- `POST /api/interactions`
- `PUT /api/interactions/{interaction_id}`

### Agent

- `POST /api/agent/run`

Accepts a user message and returns:

- the agent reply
- tool output messages produced during execution

If `GROQ_API_KEY` is missing or invalid, the endpoint returns an error.

## Development Notes

- CORS is restricted to `FRONTEND_ORIGIN`
- sample data is only inserted when no HCP records exist
- the agent uses repository-backed tools and the same application database

## Project Structure

```text
app/
  agent/
    graph.py
    tools.py
  config.py
  crud.py
  database.py
  main.py
  models.py
  schemas.py
  seed.py
requirements.txt
.env.example
```
