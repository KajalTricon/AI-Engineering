# CodebaseDocumentor

FastAPI service that:

- accepts one or more GitHub repository URLs as one logical project
- treats multiple repositories as one microservice-style project
- clones, chunks, embeds, and summarizes repositories into project-aware modules
- stores project-scoped embeddings in pgvector for cross-repository retrieval
- generates unified project documentation with overall architecture and flow diagrams
- answers project questions with retrieval-augmented generation across repositories

## Structure

`app/api`
HTTP routes.

`app/core`
Settings, database setup, lifespan hooks, and shared app-level helpers.

`app/models`
SQLAlchemy models for projects, repositories, modules, and documentation.

`app/schemas`
Request and response schemas.

`app/services`
Business logic for project submission, pipeline processing, repositories, modules, documentation, and querying.

`app/chunker`
Repository chunking logic.

`app/vector`
Embedding and pgvector similarity-search integration.

`app/agents`
LangGraph- and LangChain-based analysis and documentation workflows.

## Setup

Run the root setup script:

```bash
python3 setup.py
```

## Environment

Backend now expects Groq instead of Gemini:

```env
DATABASE_URL=...
PGVECTOR_URL=...
GROQ_API_KEY=...
```

Optional tuning:

```env
GROQ_MODEL_PRIMARY=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_MODEL_DOCUMENTATION=meta-llama/llama-4-scout-17b-16e-instruct
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5
PROJECT_QUERY_TOP_K=8
VECTOR_CHUNK_SIZE=5000
VECTOR_CHUNK_OVERLAP=500
```

## Run

Backend:

```bash
cd backend
./docai/bin/python3 -m uvicorn app.main:app --reload --port 8000
```

## API

- `POST /api/v1/projects`
  Accepts `project_name` plus `github_url` or `github_urls`.
  One repo still works; multiple repos are grouped into a single logical project.
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/modules`
- `GET /api/v1/projects/{project_id}/documentation`
- `POST /api/v1/projects/{project_id}/query`

## Notes

- Single-repo submissions are modeled as one-repository projects, so they still get module summaries, project docs, and architecture diagrams.
- Multi-repo submissions share one project status, one documentation record, and one pgvector retrieval scope.
- Module analysis stays sequential to be friendlier to free-tier rate limits.
- Project queries retrieve evidence across repositories, which enables cross-service Q&A.

## Benchmarking

A simple benchmark runner is available under `backend/benchmark`.

Sample config:
- `backend/benchmark/sample_benchmark_config.json`

Run it from the project root while the backend server is running:

```bash
cd backend
python benchmark/run_benchmark.py \
  --base-url http://localhost:8000/api/v1 \
  --config benchmark/sample_benchmark_config.json \
  --output-dir benchmark/results
```

It will:
- submit project runs
- poll until completion or failure
- optionally call the resume endpoint once on failure
- smoke-test documentation and query endpoints
- write JSON, CSV, and text summary reports

Use repeated runs across size buckets to estimate observed success rates such as 90% for a given repo size/profile.
