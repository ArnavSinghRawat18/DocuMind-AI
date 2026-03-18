# DocuMind-AI

AI-powered repository ingestion and documentation generation platform.

DocuMind-AI helps you ingest a code repository, track processing progress, and generate AI-assisted documentation from ingested code context.

## What It Does

- Accepts a repository URL and starts an asynchronous ingestion job.
- Clones and scans repository files, chunks source text, and stores metadata in MongoDB.
- Uploads chunks to a FastAPI generation service in batched requests.
- Exposes job status and health APIs through a Node.js orchestrator.
- Provides a React dashboard for ingestion, status tracking, and AI documentation prompts.

## Architecture

The current workspace is organized into three major parts:

- frontend/: React UI for submitting repos, tracking jobs, and generating docs.
- node-orchestrator/: Express API for ingestion orchestration, status, and generation routing.
- backend/: Python/FastAPI service boundary expected by the orchestrator.

High-level flow:

1. Frontend calls orchestrator POST /ingest with a repository URL.
2. Orchestrator creates a job, clones/scans/chunks files, stores chunks in MongoDB.
3. Orchestrator posts chunk batches to FastAPI /ingest.
4. Frontend polls orchestrator GET /status/:jobId for progress.
5. Frontend calls orchestrator POST /generate for AI docs.
6. Orchestrator forwards to FastAPI /generate and stores output in MongoDB.

## Implemented Orchestrator Endpoints

- POST /ingest
	- Body: { "repoUrl": "https://..." }
	- Returns: { "success": true, "jobId": "..." }
- GET /status/:jobId
	- Returns current job state from MongoDB
- POST /generate
	- Body: { "jobId": "...", "prompt": "...", "model": "llama3-70b" }
	- Returns generated document payload
- GET /health
	- Returns: { "status": "ok" }

## Key Features in Current Code

- Input validation for repository URL and generation payloads.
- Ingestion progress lifecycle with status updates and percentage progress.
- Batched chunk upload with retry and exponential backoff.
- Secret masking before external upload.
- Per-job in-memory rate limiting on generation requests.
- MongoDB persistence for jobs, chunks, and generated docs.
- Frontend UX enhancements including toasts, recent jobs, and loading skeletons.

## Environment Variables

### Node Orchestrator

Set in node-orchestrator/.env:

- MONGO_URI: MongoDB connection string (required)
- DB_NAME: Database name (default: documind_dev)
- PORT: Orchestrator port (default: 3000)
- FASTAPI_URL: FastAPI base URL (default: http://127.0.0.1:8000)
- BATCH_SIZE: Chunk upload batch size (default: 200)
- BATCH_CONCURRENCY: Parallel batch uploads (default: 2)
- BATCH_RETRIES: Retry attempts per batch (default: 3)
- BATCH_RETRY_BASE_MS: Base retry delay in ms (default: 1000)
- GENERATE_TIMEOUT_MS: /generate timeout in ms (default: 60000)

### Frontend

Set in frontend/.env:

- VITE_API_URL: Orchestrator URL (default used by UI: http://localhost:3000)

## Local Setup

### 1) Start MongoDB

Use local MongoDB or MongoDB Atlas.

### 2) Start Node Orchestrator

From node-orchestrator/:

```bash
npm install
npm run dev
```

The orchestrator starts on PORT (default 3000).

### 3) Start FastAPI Service

The orchestrator expects these FastAPI endpoints:

- POST /ingest
- POST /generate

Start your FastAPI app on FASTAPI_URL (default http://127.0.0.1:8000).

### 4) Start Frontend

From frontend/:

```bash
npm install
npm run dev
```

Open the Vite URL shown in terminal and submit a repository URL.

## Example API Calls

Start ingestion:

```bash
curl -X POST http://localhost:3000/ingest \
	-H "Content-Type: application/json" \
	-d '{"repoUrl":"https://github.com/owner/repo"}'
```

Check status:

```bash
curl http://localhost:3000/status/<jobId>
```

Generate docs:

```bash
curl -X POST http://localhost:3000/generate \
	-H "Content-Type: application/json" \
	-d '{"jobId":"<jobId>","prompt":"Generate architecture documentation","model":"llama3-70b"}'
```

## Repository Structure

```text
DocuMind-AI/
	backend/
		src/
	frontend/
		src/
			components/
			pages/
			services/
	node-orchestrator/
		db/
		routes/
		ingest.js
		server.js
	docs/
	scripts/
```

## Notes

- The orchestrator is production-oriented with retries, batching, and defensive validation.
- Generation and retrieval quality depend on the connected FastAPI/LLM backend.
- Keep credentials in .env files and never commit secrets.