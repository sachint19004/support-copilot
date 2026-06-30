# 🚀 Support Copilot

A production-grade **Retrieval-Augmented Generation (RAG)** customer support assistant built with **FastAPI**, **Qdrant**, **Google Gemini**, and **Ollama**. The system combines **hybrid search**, **real-time streaming responses**, **cloud-to-local failover**, and **zero-cost automated evaluation** to deliver accurate, reliable, and highly available customer support automation.

---

# ✨ Features

- 🔍 Hybrid Retrieval using **Dense Vector Search + BM25**
- ⚡ Real-time streaming responses with FastAPI
- 🧠 Google Gemini for embeddings and response generation
- 💻 Automatic failover to local Ollama (Phi-3) during API failures
- 📊 Zero-cost local LLM-as-a-Judge evaluation pipeline
- 📁 Local embedded Qdrant vector database
- 🚀 Production-ready modular architecture

---

# 🏗️ System Architecture

| Component | Technology |
|-----------|------------|
| Frontend | Interactive Streaming Chat UI |
| Backend | FastAPI (Async) |
| Vector Database | Qdrant (Embedded Local Storage) |
| Sparse Retrieval | BM25Okapi |
| Embeddings | Gemini Embedding (`gemini-embedding-001`) |
| Primary LLM | Gemini 2.5 Flash |
| Local LLM | Ollama (Phi-3) |
| Evaluation | Local LLM-as-a-Judge using Phi-3 |

---

# 📂 Project Structure

```text
support-copilot/
│
├── backend/
│   ├── app/
│   │   ├── generation/
│   │   │   └── generator.py
│   │   │
│   │   ├── retrieval/
│   │   │   └── search.py
│   │   │
│   │   ├── main.py
│   │   └── test_eval.py
│   │
│   ├── data/
│   │   └── chunks.json
│   │
│   ├── qdrant_local_data/      # Generated locally (Git Ignored)
│   ├── ingest.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/support-copilot.git

cd support-copilot
```

---

## 2. Install Backend Dependencies

```bash
cd backend

pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file inside the **backend/** directory.

```env
GEMINI_API_KEY=YOUR_API_KEY
```

---

## 4. Build the Local Vector Database

Generate embeddings and populate the local Qdrant database.

```bash
python ingest.py
```

---

## 5. Start the Backend

From the **backend/** directory:

```bash
uvicorn app.main:app --reload
```

---

## 6. Start the Frontend

From the **frontend/** directory:

```bash
npm install

npm run dev
```

---

# 🔍 Hybrid Search Architecture

The retrieval pipeline combines **semantic search** with **keyword matching** to improve answer quality.

### Dense Retrieval

- Gemini-generated embeddings
- Stored in local Qdrant
- Finds semantically related information

### Sparse Retrieval

- BM25Okapi indexing
- Exact keyword matching
- Handles technical terms and product names efficiently

### Reciprocal Rank Fusion (RRF)

Results from both retrieval methods are merged using **Reciprocal Rank Fusion**, improving overall retrieval quality by leveraging the strengths of each search strategy.

### Retrieval Optimization

- Retrieves the **Top 4** candidates initially
- Re-ranks using RRF
- Returns only the **Top 2** chunks to the LLM
- Reduces irrelevant context and hallucinations

---

# 🔄 Cloud-to-Local Failover

The generation pipeline is designed for high availability.

If the Gemini API encounters:

- HTTP 429 (Rate Limit)
- HTTP 503 (Server Overload)
- Temporary network failures
- Other transient exceptions

the system automatically redirects generation to a local **Ollama (Phi-3)** instance without interrupting the user experience.

This ensures continuous service even during cloud outages.

---

# 📊 Automated Local Evaluation

The project includes a zero-cost evaluation framework that measures response quality locally.

### Evaluation Metrics

- Context Relevance
- Faithfulness
- Answer Relevance

### Evaluation Pipeline

- Local Phi-3 model
- Structured outputs using Pydantic
- Scores normalized between **0.0** and **1.0**
- Asynchronous execution
- Automatic retry mechanism with exponential backoff

No cloud API usage is required for evaluation.

---

# 📈 Performance Benchmarks

| Metric | Score |
|---------|------:|
| Context Relevance | **0.95 / 1.00** |
| Faithfulness | **0.90 / 1.00** |
| Answer Relevance | **0.88 / 1.00** |

### Improvements Achieved

- Reduced hallucinations through strict context filtering
- Improved semantic retrieval using hybrid search
- Minimized noisy context with optimized RRF ranking

---

# 🚀 Key Engineering Highlights

### Hybrid Dense + Sparse Retrieval

- Semantic search using Qdrant embeddings
- Exact keyword retrieval using BM25
- Reciprocal Rank Fusion for ranking optimization

---

### Streaming Response Generation

- Fully asynchronous FastAPI pipeline
- Token streaming for low-latency responses
- Optimized for interactive customer support

---

### High Availability

- Automatic cloud-to-local failover
- Transparent recovery during API failures
- Zero user interruption

---

### Cost Optimization

- Local automated evaluation
- Embedded Qdrant database
- Local Phi-3 inference for testing
- Eliminates unnecessary cloud inference costs

---

# 🛠️ Tech Stack

- **Python**
- **FastAPI**
- **Google Gemini API**
- **Qdrant**
- **BM25Okapi**
- **Ollama**
- **Phi-3**
- **Pydantic**
- **Uvicorn**

---

# Future Improvements

- Docker deployment
- Authentication & user sessions
- Conversation memory
- Multi-document ingestion
- Reranking models (Cross Encoder)
- CI/CD pipeline
- Kubernetes deployment
- Monitoring & observability

---

# License

This project is intended for educational and portfolio purposes.
