# DocuMind AI

**AI-Powered Code Documentation Generator**  
Generate ultra-detailed, examiner-level documentation for any code repository using advanced LLMs and RAG (Retrieval-Augmented Generation).

---

## 🚀 Project Overview

DocuMind AI is an enterprise-grade, full-stack application that automates the generation of comprehensive documentation for code repositories. It leverages state-of-the-art LLMs (like Qwen2.5 via Ollama), advanced code chunking, and retrieval-augmented generation to produce documentation that meets academic, enterprise, and portfolio standards.

- **Frontend:** Modern React (Vite) SPA with dark mode, responsive UI, and real-time status feedback.
- **Backend:** FastAPI (Python) with robust RAG pipeline, MongoDB integration, and scalable architecture.
- **Orchestrator:** Node.js service for ingestion, job management, and LLM orchestration.
- **Database:** MongoDB Atlas for job, repo, and chunk metadata.

---

## 🧱 Technology Stack

- **Frontend:** React 18+, Vite, Tailwind CSS, React Router, Axios
- **Backend:** FastAPI, Pydantic, Uvicorn, PyMongo, SlowAPI (rate limiting)
- **Orchestrator:** Node.js, Express, MongoDB driver
- **Database:** MongoDB Atlas
- **LLM:** Ollama (Qwen2.5:3b or higher, local or remote)
- **Other:** Docker, dotenv, ESLint, Prettier

---

## 📁 Directory Structure

```
DocuMind-AI/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI app, routes, middleware
│   │   ├── database/      # MongoDB models, repositories
│   │   ├── generation/    # LLM client, prompt templates, generator
│   │   ├── ingestion/     # Chunker, file walker, git client
│   │   ├── retrieval/     # Retriever logic
│   │   ├── embeddings/    # Embedding service, vector store
│   │   ├── utils/         # Logger, validators
│   │   └── tests/         # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # React UI components
│   │   ├── pages/         # Main pages
│   │   ├── services/      # API calls
│   │   └── styles/        # Tailwind, custom CSS
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── node-orchestrator/
│   ├── routes/
│   ├── db/
│   ├── server.js
│   └── package.json
├── scripts/
│   └── seed_sample_data.py
├── docker-compose.yml
└── README.md
```

---

## 🎯 Features

- **Automated Documentation:** Generate README, API docs, architecture docs, or ultra-detailed examiner-level documentation.
- **RAG Pipeline:** Combines code chunk retrieval with LLMs for grounded, source-cited output.
- **Enterprise Prompting:** 21+ section master prompt for full project coverage (overview, tech stack, features, UI/UX, changelog, etc.).
- **Custom Token Limits:** Supports up to 32,000+ tokens for ultra-long documentation.
- **Job Management:** Async ingestion and generation with job status tracking.
- **Modern UI:** Responsive, dark-themed React frontend with real-time feedback.
- **Multi-Repo Support:** Ingest and document multiple repositories.
- **Source Citations:** Every fact in generated docs is traceable to code chunks.
- **Configurable:** Easily adjust chunk size, model, and prompt settings.

---

## 🏗️ Architecture

- **Frontend** communicates with backend and orchestrator via REST APIs.
- **Backend** handles RAG, LLM prompt building, and documentation generation.
- **Orchestrator** manages ingestion, job status, and LLM requests.
- **MongoDB** stores job metadata, code chunks, and repo info.
- **Ollama** (or other LLM provider) runs locally or remotely for fast, private inference.

---

## 🔧 Installation & Setup

### Prerequisites

- Node.js 18+
- Python 3.10+
- MongoDB Atlas account (or local MongoDB)
- Ollama installed with Qwen2.5 model pulled (`ollama pull qwen2.5:3b`)
- Docker (optional, for containerized setup)

### Steps

1. **Clone the repository:**
	```sh
	git clone https://github.com/ArnavSinghRawat18/DocuMind-AI.git
	cd DocuMind-AI
	```

2. **Backend Setup:**
	```sh
	cd backend
	pip install -r requirements.txt
	# Configure .env for MongoDB and Ollama
	python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
	```

3. **Frontend Setup:**
	```sh
	cd ../frontend
	npm install
	npm run dev
	# Open http://localhost:5173 (or next available port)
	```

4. **Node Orchestrator:**
	```sh
	cd ../node-orchestrator
	npm install
	node server.js
	```

5. **Ollama LLM:**
	```sh
	ollama serve
	ollama pull qwen2.5:3b
	```

6. **Access the App:**
	- Frontend: http://localhost:5173
	- Backend API: http://localhost:8000/docs

---

## 📦 NPM/Yarn Scripts

- `npm run dev` – Start frontend in development mode
- `npm run build` – Build frontend for production
- `npm test` – Run frontend tests
- `node server.js` – Start orchestrator service

---

## 🌐 Deployment

- Use Docker Compose for full stack deployment.
- Configure environment variables for production (MongoDB, Ollama, etc.).
- Supports deployment on any cloud or on-prem server.

---

## 📱 Mobile Optimization

- Fully responsive UI (320px+)
- Touch-friendly controls
- Mobile navigation and dialogs

---

## 🔄 Changelog & Development History

- See GitHub commit history for all major updates, bug fixes, and feature additions.

---

## 🐛 Known Issues

- Large repos may require increased chunk size or memory.
- Ollama model context window must match `max_tokens` for ultra-long docs.
- "Mock embeddings" warning in dev mode (safe to ignore for local testing).

---

## 🎯 Future Enhancements

- Multi-model support (OpenAI, Groq, etc.)
- User authentication and history
- PDF/Markdown export
- More advanced RAG chunking and summarization

---

## 🤝 Contribution Guidelines

- Fork the repo, create a feature branch, submit PRs.
- Follow PEP8 (Python) and Airbnb (JS) style guides.
- Add tests for new features.

---

## 🔐 License

This project is for educational and personal portfolio use.  
Contact the owner for commercial licensing.

---

## 🙏 Acknowledgments

- Qwen2.5, Ollama, FastAPI, React, MongoDB, Tailwind CSS, and the open-source community.

---

**For any issues or feature requests, open an issue on GitHub or contact the maintainer.**