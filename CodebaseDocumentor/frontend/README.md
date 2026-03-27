# Frontend Setup

## What this frontend does

This React + Vite app is wired to the FastAPI backend in `../backend`.

Flow:

1. Home page submits a GitHub repository URL to `POST /api/v1/repositories`
2. Processing page polls `GET /api/v1/repositories/{repo_id}`
3. Dashboard loads:
   - `GET /api/v1/repositories/{repo_id}/documentation`
   - `GET /api/v1/repositories/{repo_id}/modules`
4. Q&A sends questions to `POST /api/v1/repositories/{repo_id}/query`

## Environment

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Default:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Run the backend

From `../backend`:

```bash
source docai/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Install frontend dependencies

From this folder:

```bash
npm install
```

## Run the frontend

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

## Build for production

```bash
npm run build
```

## Notes

- The backend now enables CORS for Vite dev on port `5173`.
- Generated documentation is shown inside the dashboard in an iframe using the backend static URL.
- If you change the backend port, update `VITE_API_BASE_URL` in `.env`.
