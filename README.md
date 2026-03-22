# 🛡️ Fraud Sentinel — Gen AI Fraud Detection System

A full-stack Gen AI application for real-time fraud detection using **Groq LLM**, **FAISS vector database**, **RAG (Retrieval-Augmented Generation)**, **FastAPI**, and **React**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   REACT FRONTEND                         │
│  Dashboard │ Analyze (RAG) │ Knowledge Base              │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (axios)
┌────────────────────▼────────────────────────────────────┐
│                  FASTAPI BACKEND                         │
│                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │ Transaction  │   │  FAISS RAG   │   │  Groq LLM   │  │
│  │ Generator   │   │  Engine      │   │  Analyzer   │  │
│  │ (Groq LLM)  │   │  (256-dim)   │   │ (Llama 70B) │  │
│  └─────────────┘   └──────────────┘   └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### RAG Pipeline
```
Transaction Query
      │
      ▼
TF-IDF Embedding (256-dim)
      │
      ▼
FAISS IndexFlatIP (cosine similarity)
      │
      ▼
Top-4 Relevant Fraud Patterns Retrieved
      │
      ▼
Groq Llama-3.3-70B + RAG Context
      │
      ▼
Structured JSON: risk_score, fraud_pattern,
explanation, actions, recovery_steps, SAR flag
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### 1. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
cp .env.example .env
npm install
npm start
```

App runs at **http://localhost:3000**
API docs at **http://localhost:8000/docs**

### 3. Docker (Full Stack)

```bash
cp backend/.env.example .env
# Set GROQ_API_KEY in .env
docker-compose up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Analyze structured transaction with RAG |
| `POST` | `/api/analyze-text` | Analyze free-text description |
| `POST` | `/api/generate-transactions` | LLM-generate synthetic transactions |
| `GET`  | `/api/dashboard/stats` | Dashboard KPIs and charts data |
| `GET`  | `/api/rag/knowledge-base` | List RAG knowledge entries |
| `GET`  | `/health` | Health check |

---

## 🧠 RAG Knowledge Base

12 expert fraud pattern documents indexed in FAISS:

| ID | Pattern | Key Signals |
|----|---------|-------------|
| ATO_001 | Account Takeover | New device + geo anomaly + unusual hour |
| CNP_002 | Card-Not-Present | Address mismatch + failed CVV |
| GEO_003 | Geo Anomaly | Impossible travel + sanctioned country |
| VEL_004 | Velocity Attack | 3+ txns in 10 min |
| SYN_005 | Synthetic Identity | Thin credit + bust-out |
| TOR_006 | TOR Network | 185.220.x.x exit nodes |
| PHISH_007 | Phishing | Post-reset wire transfer |
| CRYPTO_008 | Crypto Fraud | Irreversible + first-time |
| SAR_009 | SAR Requirements | BSA thresholds |
| SKIM_010 | Card Skimming | Clone card + different city |
| FRIENDLY_011 | Friendly Fraud | Chargeback abuse |
| ELDER_012 | Elder Abuse | Age 65+ + large withdrawal |

---

## 🎯 Features

### Dashboard
- KPI cards: total analyzed, flagged today, high-risk count, SAR pending
- Weekly volume area chart (flagged vs. cleared)
- Risk distribution pie chart
- Top fraud patterns bar chart
- Recent alerts feed

### Analyze Page
- **LLM-Generated Mode**: Groq generates realistic synthetic transactions
- **Custom Text Mode**: Paste any description for instant RAG analysis
- Risk score gauge (0–100) with animated fill
- 4 analysis tabs: Explanation, Actions, Recovery, Technical
- RAG source attribution (which knowledge docs influenced the result)
- SAR filing flag with regulatory guidance
- Customer alert message generation

### Knowledge Base
- Browse all 12 indexed fraud pattern documents
- Search/filter by category or keyword
- Vector embedding metadata display
- FAISS index stats (dimensions, similarity metric)

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq API (Llama-3.3-70B-Versatile) |
| **Vector DB** | FAISS (IndexFlatIP, 256-dim) |
| **RAG** | Custom TF-IDF embedder + FAISS retrieval |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | React 18 + React Router + Recharts |
| **HTTP Client** | Axios |
| **Container** | Docker + Docker Compose |

---

## 🔑 Environment Variables

### Backend (`backend/.env`)
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### Frontend (`frontend/.env`)
```
REACT_APP_API_URL=http://localhost:8000
```

---

## 📁 Project Structure

```
fraud-sentinel/
├── backend/
│   ├── main.py                 # FastAPI app + routes
│   ├── rag_engine.py           # FAISS RAG engine
│   ├── groq_client.py          # Groq LLM integration
│   ├── transaction_generator.py # LLM transaction synthesis
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js              # Router + nav
│   │   ├── pages/
│   │   │   ├── Dashboard.js    # Charts + KPIs
│   │   │   ├── Analyze.js      # RAG analyzer
│   │   │   └── KnowledgeBase.js
│   │   └── utils/api.js        # API client
│   ├── public/index.html
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
└── README.md
```
