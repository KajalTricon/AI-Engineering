# CodebaseDocumentor

FastAPI service that:

- accepts a GitHub repository URL
- clones and chunks the repository
- stores module content and embeddings
- generates module summaries and project documentation
- answers repository questions with retrieval-augmented generation

## Structure

`app/api`
HTTP routes.

`app/core`
Settings, database setup, lifespan hooks, and shared app-level helpers.

`app/models`
SQLAlchemy models.

`app/schemas`
Request and response schemas.

`app/services`
Business logic for repositories, pipeline processing, modules, documentation, and querying.

`app/chunker`
Repository chunking logic.

`app/vector`
Embedding and similarity-search integration.

`app/agents`
LLM-driven analysis and documentation generation workflows.

## Setup

Run the root setup script:

```bash
python3 setup.py
```

This bootstraps:

- backend virtual environment and Python dependencies
- backend/frontend `.env` files from examples when missing
- frontend npm dependencies when Node.js is installed

## Run

Backend:

```bash
cd backend
./docai/bin/python3 -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

## API

- `POST /api/v1/repositories`
- `GET /api/v1/repositories/{repo_id}`
- `GET /api/v1/repositories/{repo_id}/modules`
- `GET /api/v1/repositories/{repo_id}/documentation`
- `POST /api/v1/repositories/{repo_id}/query`
