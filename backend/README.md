# DocuMind AI Backend

AI-powered documentation generation from code repositories.

## Phase 1: Ingestion Pipeline

The backend implements a complete ingestion pipeline that:
1. Clones GitHub repositories
2. Scans for supported files (.py, .js, .ts, .md)
3. Parses file contents with encoding detection
4. Chunks content into ~800 token segments
5. Stores chunks in MongoDB

## Quick Start

### Prerequisites
- Python 3.11+
- MongoDB 7.0+
- Git

### Local Development

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection string
   ```

3. **Start MongoDB:**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name documind-mongo mongo:7.0
   ```

4. **Run the server:**
   ```bash
   uvicorn src.api.main:app --reload
   ```

5. **Access the API:**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Using Docker Compose

```bash
# From project root
docker-compose up -d
```

## API Endpoints

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingest` | Start repository ingestion |
| GET | `/api/v1/jobs/{job_id}` | Get job status |
| GET | `/api/v1/jobs` | List all jobs |
| GET | `/api/v1/jobs/{job_id}/chunks` | Get chunks for a job |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |

## Example Usage

### Ingest a Repository

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo"}'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Ingestion started for owner/repo"
}
```

### Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "repo_url": "https://github.com/owner/repo",
  "repo_name": "repo",
  "stats": {
    "total_files": 25,
    "processed_files": 25,
    "total_chunks": 150,
    "total_lines": 5000
  }
}
```

## Project Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── main.py           # FastAPI application
│   │   ├── dependencies.py   # Dependency injection
│   │   └── routes/
│   │       └── ingestion.py  # Ingestion endpoints
│   ├── database/
│   │   ├── models.py         # Pydantic models
│   │   ├── mongodb.py        # MongoDB connection
│   │   └── repositories.py   # Data access layer
│   ├── ingestion/
│   │   ├── git_client.py     # Git clone functionality
│   │   ├── file_walker.py    # File scanning
│   │   ├── parser.py         # File parsing
│   │   └── chunker.py        # Text chunking
│   ├── utils/
│   │   ├── logger.py         # Logging utilities
│   │   └── validators.py     # Input validation
│   └── config.py             # Configuration
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Job Status Flow

```
pending → cloning → scanning → parsing → chunking → storing → completed
                                                            ↓
                                                         failed
```

## Phase 2: Embeddings & Retrieval Pipeline

The backend now includes a complete embedding and retrieval pipeline for RAG:
1. Generate vector embeddings from code chunks (OpenAI or mock)
2. Store embeddings in MongoDB with vector search support
3. Semantic search across code chunks
4. RAG-ready context retrieval

### Retrieval API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/retrieve` | Retrieve relevant chunks for a query |
| POST | `/api/v1/embed/{job_id}` | Generate embeddings for all chunks in a job |
| GET | `/api/v1/embed/{job_id}/stats` | Get embedding statistics for a job |
| GET | `/api/v1/search/{job_id}` | Search chunks within a specific job |

### Retrieval Example Usage

#### Generate Embeddings for a Job

```bash
curl -X POST http://localhost:8000/api/v1/embed/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_chunks": 150,
  "embedded_chunks": 150,
  "status": "completed",
  "message": "Embeddings generated successfully"
}
```

#### Get Embedding Stats

```bash
curl http://localhost:8000/api/v1/embed/550e8400-e29b-41d4-a716-446655440000/stats
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_chunks": 150,
  "embedded_chunks": 150,
  "embedding_coverage": 1.0,
  "embedding_dimensions": 1536
}
```

#### Retrieve Relevant Chunks (RAG)

```bash
curl -X POST http://localhost:8000/api/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the authentication middleware work?",
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "query": "How does the authentication middleware work?",
  "matches": [
    {
      "chunk_id": "chunk-123",
      "content": "def authenticate(request):\n    token = request.headers.get('Authorization')...",
      "file_path": "src/middleware/auth.py",
      "similarity_score": 0.92,
      "start_line": 15,
      "end_line": 45,
      "language": "python"
    }
  ],
  "total_matches": 5
}
```

#### Search Within a Job

```bash
curl "http://localhost:8000/api/v1/search/550e8400-e29b-41d4-a716-446655440000?query=database+connection&top_k=3"
```

### MongoDB Atlas Vector Search Setup

To use MongoDB Atlas Vector Search for optimal similarity search performance:

1. **Create a Vector Search Index** in MongoDB Atlas:
   - Go to Atlas UI → Database → Browse Collections → Search Indexes
   - Create Index with this JSON configuration:

   ```json
   {
     "fields": [
       {
         "type": "vector",
         "path": "embedding",
         "numDimensions": 1536,
         "similarity": "cosine"
       }
     ]
   }
   ```

2. **Name the index** `vector_index` (or update `VECTOR_SEARCH_INDEX_NAME` in `.env`)

If no vector index is configured, the system falls back to in-memory similarity search.

## MongoDB Collections

- `jobs` - Ingestion job metadata
- `code_chunks` - Parsed and chunked code
- `embeddings` - Vector embeddings for code chunks

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| MONGODB_URI | mongodb://localhost:27017 | MongoDB connection string |
| MONGODB_DATABASE | documind | Database name |
| API_HOST | 0.0.0.0 | API host |
| API_PORT | 8000 | API port |
| LOG_LEVEL | INFO | Logging level |
| DATA_DIR | ./data | Data storage directory |
| OPENAI_API_KEY | - | OpenAI API key for embeddings |
| USE_MOCK_EMBEDDINGS | true | Use mock embeddings for testing |
| EMBEDDING_DIMENSIONS | 1536 | Embedding vector dimensions |
| VECTOR_SEARCH_INDEX_NAME | vector_index | MongoDB Atlas Vector Search index name |
| SIMILARITY_THRESHOLD | 0.7 | Minimum similarity score for results |

## License

MIT
