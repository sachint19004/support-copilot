# 🤖 Support Copilot

> **Helping customer-support teams answer questions using their own knowledge base while reducing irrelevant context, unsupported answers, and dependence on a single AI provider.**

Customer-support teams often have to work with product documentation, troubleshooting guides, policies, FAQs, and internal knowledge bases.

The challenge is not simply generating an answer.

A useful support assistant needs to answer questions using the **right information**, while avoiding irrelevant context and unsupported claims. It also needs to remain usable when an external AI API is temporarily unavailable.

**Support Copilot** is a Retrieval-Augmented Generation (RAG) customer-support assistant designed around these problems.

Instead of sending a customer question directly to an LLM, the system first retrieves relevant information from a knowledge base, combines different retrieval strategies, filters the context, and then generates a response using that context.

```text
Customer Question
        │
        ▼
   Hybrid Search
   ┌────┴────┐
   ▼         ▼
 Dense      BM25
 Search    Search
   │         │
   └────┬────┘
        ▼
       RRF
        │
        ▼
   Top Context
        │
        ▼
      LLM
        │
        ▼
Grounded Response
```

The system also includes cloud-to-local model failover and a local evaluation pipeline so that reliability and response quality can be tested without continuously depending on external inference services.

## 🎯 Problem

A direct LLM workflow looks like:

```text
User Question
      │
      ▼
      LLM
      │
      ▼
Generated Answer
```

This approach can fail when the model:

- Does not contain the required information
- Misinterprets the question
- Uses irrelevant knowledge
- Produces an answer that sounds plausible but isn't supported by the organization's documentation

For customer support, a more useful workflow is:

```text
User Question
      │
      ▼
Knowledge Retrieval
      │
      ▼
Relevant Context
      │
      ▼
      LLM
      │
      ▼
Grounded Answer
```

Support Copilot therefore focuses heavily on retrieval quality and context selection, rather than treating generation as the only important component.

## 💡 What Support Copilot Does

The system:

- Retrieves relevant information from a knowledge base
- Uses both dense semantic search and sparse keyword search
- Combines retrieval results using Reciprocal Rank Fusion
- Reduces the retrieved context before sending it to the LLM
- Generates responses using Google Gemini
- Streams responses through an asynchronous FastAPI backend
- Automatically falls back to a local Ollama/Phi-3 model during transient Gemini failures
- Evaluates responses locally using an LLM-as-a-Judge pipeline

The result is a support assistant designed around:

**relevance → grounding → reliability → evaluation**

## ✨ Features

- 🔍 Hybrid Retrieval using Dense Vector Search + BM25
- ⚡ Real-time streaming responses with FastAPI
- 🧠 Google Gemini for embeddings and response generation
- 💻 Automatic failover to local Ollama (Phi-3) during API failures
- 📊 Zero-cost local LLM-as-a-Judge evaluation pipeline
- 📁 Local embedded Qdrant vector database
- 🚀 Modular architecture designed for extension

## 🏗️ System Architecture

| Component | Technology |
|---|---|
| Frontend | Interactive Streaming Chat UI |
| Backend | FastAPI (Async) |
| Vector Database | Qdrant (Embedded Local Storage) |
| Sparse Retrieval | BM25Okapi |
| Embeddings | Gemini Embedding (gemini-embedding-001) |
| Primary LLM | Gemini 2.5 Flash |
| Local LLM | Ollama (Phi-3) |
| Evaluation | Local LLM-as-a-Judge using Phi-3 |

## 🔍 Hybrid Search Architecture

The retrieval pipeline combines semantic search with keyword matching.

The reason for using both approaches is that customer-support queries can contain both:

- Concepts that require semantic understanding
- Exact product names, error messages, or technical terminology

### Dense Retrieval

Dense retrieval uses Gemini-generated embeddings.

The embeddings are:

- Generated using Gemini
- Stored in local Qdrant
- Used to identify semantically related information

For example:

**Question:** "How do I regain access to my account?"
    ↓
Dense Retrieval


Finds conceptually related content such as:

- "Resetting a forgotten password"
- "Recovering an account"
- "Account access troubleshooting"

The exact wording does not need to match.

### Sparse Retrieval

Sparse retrieval uses BM25Okapi.

It is particularly useful for:

- Exact keywords
- Product names
- Technical terminology
- Error messages
- Feature names

For example:

**Query:** "Error E1042 during payment"
    ↓
   BM25

   
Prioritizes documents containing: "E1042", "payment", "error"

## 🔀 Reciprocal Rank Fusion (RRF)

The results from both retrieval methods are combined using Reciprocal Rank Fusion.

```text
                 User Query
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   Dense Retrieval        BM25 Retrieval
      Qdrant                 Keywords
          │                     │
          └──────────┬──────────┘
                     ▼
               RRF Ranking
                     │
                     ▼
              Top Candidates
                     │
                     ▼
              Selected Context
                     │
                     ▼
                    LLM
                     │
                     ▼
               Final Answer
```

This allows the system to benefit from both:

- Semantic similarity
- Exact keyword matching

## 🎯 Retrieval Optimization

The system initially retrieves **Top 4 candidates**.

These candidates are then re-ranked using Reciprocal Rank Fusion.

Only **Top 2 chunks** are finally passed to the LLM.

```text
Knowledge Base
      │
      ▼
Top 4 Candidates
      │
      ▼
RRF Re-ranking
      │
      ▼
Top 2 Contexts
      │
      ▼
LLM
```

The purpose is to reduce irrelevant context reaching the generation model.

More retrieved information does not automatically mean a better answer.

The system therefore treats context selection as an important part of RAG quality.

## 🔄 Cloud-to-Local Failover

The generation pipeline is designed for high availability.

The primary generation model is Google Gemini.

If the Gemini API encounters:

- HTTP 429 — Rate Limit
- HTTP 503 — Server Overload
- Temporary network failures
- Other transient exceptions

the system automatically redirects generation to a local Ollama/Phi-3 instance.

```text
                   User Question
                         │
                         ▼
                  Gemini Generation
                         │
                 ┌───────┴───────┐
                 │               │
              Success          Failure
                 │               │
                 ▼               ▼
             Response       Ollama / Phi-3
                                 │
                                 ▼
                              Response
```

The goal is to avoid exposing transient cloud-provider failures directly to the user.

## ⚡ Streaming Response Generation

Customer support is an interactive workflow.

Waiting for an entire generated response before showing anything can make the system feel slower than necessary.

The backend therefore uses an asynchronous FastAPI pipeline with token streaming.

```text
User
 │
 ▼
FastAPI
 │
 ▼
Hybrid Retrieval
 │
 ▼
Context Selection
 │
 ▼
Generation
 │
 ▼
Token Stream
 │
 ▼
Interactive UI
```

This allows generated content to be delivered progressively.

## 📊 Automated Local Evaluation

A RAG system needs to be evaluated beyond simply asking whether the response "looks good."

Support Copilot includes a local evaluation framework that measures:

- Context Relevance
- Faithfulness
- Answer Relevance

The evaluation uses a local Phi-3 model as an LLM judge.

```text
Generated Response
        │
        ▼
Local Phi-3 Judge
        │
 ┌──────┼──────────┐
 ▼      ▼          ▼
Context Faithfulness Answer
Relevance            Relevance
```

The pipeline includes:

- Local Phi-3 model
- Structured outputs using Pydantic
- Scores normalized between 0.0 and 1.0
- Asynchronous execution
- Automatic retry mechanism
- Exponential backoff

No cloud API usage is required for the evaluation stage.

## 📈 Performance Benchmarks

The current evaluation produced:

| Metric | Score |
|---|---|
| Context Relevance | 0.95 / 1.00 |
| Faithfulness | 0.90 / 1.00 |
| Answer Relevance | 0.88 / 1.00 |

**Improvements Achieved**
- Reduced hallucinations through strict context filtering
- Improved semantic retrieval using hybrid search
- Minimized noisy context with optimized RRF ranking

These metrics are evaluation results for the current project configuration and should be interpreted within the scope of the local evaluation dataset and pipeline.

## 🚀 Key Engineering Highlights

**Hybrid Dense + Sparse Retrieval**
- Semantic search using Qdrant embeddings
- Exact keyword retrieval using BM25
- Reciprocal Rank Fusion for ranking optimization

**Streaming Response Generation**
- Fully asynchronous FastAPI pipeline
- Token streaming for low-latency responses
- Optimized for interactive customer support

**High Availability**
- Automatic cloud-to-local failover
- Transparent recovery during API failures
- Local fallback inference using Phi-3

**Cost Optimization**
- Local automated evaluation
- Embedded Qdrant database
- Local Phi-3 inference for testing
- Reduced dependency on additional cloud inference during evaluation

## 📂 Project Structure

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

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sachint19004/support-copilot.git
cd support-copilot
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file inside the `backend/` directory.

```env
GEMINI_API_KEY=YOUR_API_KEY
```

### 4. Build the Local Vector Database

Generate embeddings and populate the local Qdrant database.
```bash
python ingest.py
```

### 5. Start the Backend

From the `backend/` directory:
```bash
uvicorn app.main:app --reload
```

### 6. Start the Frontend

From the `frontend/` directory:
```bash
npm install
npm run dev
```

## 🧠 Design Decisions

**Why RAG instead of direct LLM generation?**

Customer-support answers should be grounded in a controlled knowledge source.

RAG allows the system to retrieve relevant information before generation rather than relying entirely on the model's internal knowledge.

**Why hybrid retrieval?**

Dense retrieval is useful for semantic similarity.

BM25 is useful for exact terms.

Customer-support queries can require both.

Combining the two through RRF allows the system to use their complementary strengths.

**Why Top 4 → Top 2?**

Retrieving more context is not automatically better.

Irrelevant context can make generation less reliable.

The system therefore:

```text
Top 4
  ↓
RRF
  ↓
Top 2
  ↓
LLM
```

This intentionally reduces the amount of context passed to the model.

**Why local failover?**

External APIs can experience:

- Rate limits
- Service overload
- Network problems
- Temporary outages

A local Phi-3 model provides a fallback generation path.

**Why local evaluation?**

Evaluating every response through another cloud API introduces additional cost and dependency.

Using a local model makes repeated evaluation easier to run during development.

## 🛠️ Tech Stack

- Python
- FastAPI
- Google Gemini API
- Qdrant
- BM25Okapi
- Ollama
- Phi-3
- Pydantic
- Uvicorn

## 🔮 Future Improvements

Potential future extensions include:

- Docker deployment
- Authentication & user sessions
- Conversation memory
- Multi-document ingestion
- Reranking models using Cross Encoders
- CI/CD pipeline
- Kubernetes deployment
- Monitoring & observability

## 📜 License

This project is intended for educational and portfolio purposes.
