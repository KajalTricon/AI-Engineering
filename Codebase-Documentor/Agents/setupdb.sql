-- Run once:  psql -U postgres -f setup_db.sql
-- Then start the app — SQLAlchemy creates all tables automatically.

CREATE DATABASE codebase_docs;
\c codebase_docs

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────
-- pgvector install (if not already installed)
--
-- Ubuntu/Debian:
--   sudo apt install postgresql-server-dev-all build-essential
--   git clone https://github.com/pgvector/pgvector.git
--   cd pgvector && make && sudo make install
--
-- macOS:
--   brew install pgvector
-- ─────────────────────────────────────────────────────────────