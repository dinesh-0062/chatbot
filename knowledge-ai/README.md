# Knowledge AI

Knowledge AI is a FastAPI and React document intelligence application for indexing PDFs and public documentation pages, then answering questions with retrieved source citations.

## Stack

- FastAPI, SQLAlchemy, PostgreSQL/Neon
- ChromaDB and all-MiniLM-L6-v2 embeddings
- Groq for answer generation
- React 19, Vite, Bootstrap 5

## Setup

1. Create the environment file:

   ```bash
   cp .env.example .env
   ```

2. Set `DATABASE_URL` and `GROQ_API_KEY`. Keep the real `.env` private.

3. Install backend dependencies:

   ```bash
   cd knowledge-ai
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Initialize the database and start FastAPI:

   ```bash
   python app/init_db.py
   uvicorn app.main:app --reload
   ```

   FastAPI is available at `http://localhost:8000`; Swagger is at `/docs`.

5. Install and start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Configuration

Key settings are documented in `.env.example`:

- `DATABASE_URL`: PostgreSQL or Neon connection URL
- `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_FALLBACK_MODEL`
- `CHROMA_PERSIST_DIRECTORY`, `EMBEDDING_MODEL`
- `TOP_K`, `SIMILARITY_THRESHOLD`, `MAX_RAG_CONTEXT_CHARS`
- `MAX_UPLOAD_SIZE_MB`, `MAX_URL_CONTENT_SIZE_MB`, `REQUEST_TIMEOUT_SECONDS`
- `FRONTEND_ORIGINS`, `VITE_API_BASE_URL`

## API

- `POST /documents/upload`
- `GET /documents/`
- `DELETE /documents/{document_id}`
- `POST /sources/url`
- `GET /sources/`
- `GET /sources/{source_id}`
- `POST /sources/{source_id}/refresh`
- `DELETE /sources/{source_id}`
- `POST /chat/ask`
- `POST /conversations/`
- `GET /conversations/`
- `GET /conversations/{conversation_id}`
- `PATCH /conversations/{conversation_id}`
- `DELETE /conversations/{conversation_id}`

## Testing

```bash
cd knowledge-ai
INITIALIZE_DATABASE=false pytest -q
cd frontend
npm run build
npm run lint
```

Basic tests do not require a live Groq API key or external website access.

## Security

Website ingestion accepts public HTTP/HTTPS URLs only. Localhost, loopback, private, link-local, reserved, multicast, and unresolved addresses are blocked. Responses are time-limited and size-limited, and redirects are validated. The app does not execute JavaScript or bypass robots.txt restrictions.
