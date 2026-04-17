# LexIndex - Live Google Docs RAG & Intelligent Document Q&A

A production-ready RAG (Retrieval-Augmented Generation) system that enables semantic search, question-answering, and real-time synchronization over Google Docs and static files with full transparency into the retrieval process.

## 🎯 System Overview

LexIndex implements a **two-stage retrieval pipeline** (page/section-level indexing combined with chunk-level search) and features a **Live Google Docs Sync Engine**. It delivers accurate, grounded answers that automatically update when your source documents change.

### Architecture

#### High-Level System Flow

``` text
┌──────────────────────────────────────────────────────────────────────────────┐
│                               FRONTEND (React + Vite)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ UploadPanel  │  │QueryInterface│  │  AnswerCard  │  │   SyncIndicator  │  │
│  │              │  │              │  │              │  │                  │  │
│  │ • File drop  │  │ • Text input │  │ • LLM answer │  │ • Live status of │  │
│  │ • GDoc Link  │  │ • Submit     │  │ • Citations  │  │   connected docs │  │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘  └─────────▲────────┘  │
│         │                 │                 │                    │           │
└─────────┼─────────────────┼─────────────────┼────────────────────┼───────────┘
          │ POST            │ POST            │ Response           │ GET
          │ /connect-gdoc   │ /query          │                    │ /sync-status
          ▼                 ▼                 │                    │
┌─────────────────────────────────────────────┴────────────────────┴───────────┐
│                           FASTAPI BACKEND (Python)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                         ROUTERS (API Endpoints)                       │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │  /api/upload      /api/connect-gdoc     /api/query   /api/sync-status │   │
│  └───────┬────────────────────┬─────────────────┬────────────────┬───────┘   │
│          │                    │                 │                │           │
│          ▼                    ▼                 ▼                ▼           │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                           SERVICES LAYER                              │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  1. INGESTION & PARSING                                               │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │  │ google_docs.py: fetch_doc() → parse_into_sections() (by H1/H2)   │ │   │
│  │  │ ingestion.py:   parse_pdf/txt() → _chunk_page()                  │ │   │
│  │  └─────────────────────────────────┬────────────────────────────────┘ │   │
│  │                                    ▼                                  │   │
│  │  2. LIVE SYNC ENGINE (sync.py & poller.py)                            │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │  │ Background loop runs every N seconds (default: 60s)              │ │   │
│  │  │ - Fetches connected GDocs                                        │ │   │
│  │  │ - Computes MD5 Hash per section                                  │ │   │
│  │  │ - Compares Hash vs Pinecone state                                │ │   │
│  │  │ - Surgically Adds / Updates / Deletes vectors in Pinecone        │ │   │
│  │  └─────────────────────────────────┬────────────────────────────────┘ │   │
│  │                                    ▼                                  │   │
│  │  3. PINECONE INDEXER (indexer.py)                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │  │ add_chunks() -> Upsert to 'chunks' namespace                     │ │   │
│  │  │ add_page_summary() -> Upsert to 'page-index' namespace           │ │   │
│  │  │ Structured Metadata: {doc_id, section_id, content_hash}          │ │   │
│  │  └─────────────────────────────────┬────────────────────────────────┘ │   │
│  │                                    ▼                                  │   │
│  │  4. TWO-STAGE RETRIEVAL (page_index.py)                               │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │  │ STAGE 1: query_page_index() -> Get Top-K Sections/Pages          │ │   │
│  │  │ STAGE 2: query_chunks() -> Get Top-K Chunks filtered by Stage 1  │ │   │
│  │  └─────────────────────────────────┬────────────────────────────────┘ │   │
│  │                                    ▼                                  │   │
│  │  5. LLM SERVICE (llm.py)                                              │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │  │ generate_answer(question, chunks[]) → Groq Inference (Llama 3)   │ │   │
│  │  └──────────────────────────────────────────────────────────────────┘ │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                          EXTERNAL DEPENDENCIES                        │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌──────────────────────────┐   │   │
│  │  │ Pinecone       │ │ Groq API       │ │ Google Docs API          │   │   │
│  │  │ (Vector DB)    │ │ (Inference)    │ │ (content.readonly)       │   │   │
│  │  ├────────────────┤ ├────────────────┤ ├──────────────────────────┤   │   │
│  │  │ • Serverless   │ │ • Llama-3.3    │ │ • Service Account Auth   │   │   │
│  │  │ • Namespaces   │ │ • 8b summaries │ │ • REST JSON extraction   │   │   │
│  │  └────────────────┘ └────────────────┘ └──────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔥 Features & How it Works

### Live Google Docs Hash-Sync
Instead of re-embedding an entire document when one sentence changes, LexIndex uses an intelligent diffing engine:
1. When a Doc is connected, it gets split by naturally occurring headings (`Heading 1` / `Heading 2`).
2. Each section's body text is hashed using `MD5`. The hash is stored as metadata in **Pinecone**.
3. An asynchronous background poller (`poller.py`) fetches the document every 60 seconds.
4. It compares new hashes to stored hashes. It will perfectly orchestrate updates by computing:
   - **Adds**: New sections
   - **Updates**: Modified sections (hash mismatch)
   - **Deletions**: Sections removed from the doc
   
### Two-Stage Retrieval 
- **Stage 1 (Section Index)**: The system summarizes each file page or Google Doc section with a fast LLM (Llama 3 8B). Summaries are embedded into the `page-index` Pinecone namespace. Queries hit this index first to surface highly relevant logical boundaries.
- **Stage 2 (Chunk Search)**: The system filters semantic chunk search strictly to the sections identified in Stage 1, eliminating cross-document noise and preventing the LLM from hallucinating on completely unrelated chunks.

---

## 🚀 Setup & Execution

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key
- Pinecone API Key
- Google Cloud Service Account (`credentials.json`)

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
# API Keys
GROQ_API_KEY=gsk_your_groq_key
PINECONE_API_KEY=pcsk_your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1

# Important Settings
FRONTEND_URLS=http://localhost:5173,http://localhost:5174
GOOGLE_CREDENTIALS_PATH=./credentials.json
POLL_INTERVAL_SECONDS=60
```

> **Note**: Place your Google Service Account `credentials.json` directly inside the `backend/` directory. It is explicitly ignored in `.gitignore` for safety. Remember to **Share** your Google Docs with the service account email before pasting them into the app!

Run the FastAPI backend:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend/` directory (if you aren't deploying on the same domain):
```env
VITE_BACKEND_URL=http://localhost:8000
```

Run the Vite dev server:
```bash
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## ☁️ Deployment Guidelines (e.g. AWS EC2)

For cloud instance deployments:
1. `git clone` the repository onto the instance. 
2. Use `scp`, `sftp`, or a terminal editor (`nano credentials.json`) to recreate your `credentials.json` file inside the `backend/` directory since pushing it to GitHub is disabled.
3. Use a production ASGI runner like `gunicorn` combined with `uvicorn.workers.UvicornWorker` instead of just using `--reload`.
4. The background asyncio polling task automatically binds to the Uvicorn/FastAPI startup lifecycle (`lifespan`).

---

## 🛠️ Key Design Decisions

1. **Pinecone over ChromaDB**
   - We migrated from ChromaDB (localStorage) to Pinecone Serverless to support robust multi-namespace deployments (`chunks` and `page-index` partitions) and to dramatically reduce EC2 scaling limitations since vector persistence is now offloaded.
   
2. **Groq Llama-3**
   - Generating short summaries for every logical section requires speed. Groq provides near-instant LLM generation. By routing Summaries to `llama-3.1-8b-instant` and complex logic inference Answers to `llama-3.3-70b-versatile`, cost and speed are balanced.

3. **Background Asyncio Sync**
   - Sync polling is managed via Python `asyncio` tied to FastAPI's `@asynccontextmanager lifespan`. This allows the server to simultaneously field user requests and maintain live indexing without blocking threads or requiring painful architecture overhead (e.g., celery/redis workers).

---

## 📝 License

MIT License - feel free to use, modify, and distribute.

**Built with zeal for transparent, grounded AI.**
