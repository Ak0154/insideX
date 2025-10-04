
# 📊 insideX: AI-Powered Stock Anomaly Detector

insideX is an **AI-driven platform** that monitors financial news, detects anomalies, and provides **threat-level insights (0–10)** for stocks in real-time.
It combines **Perplexity AI** for latest news, **Pathway** for memory & vector retrieval, **Claude AI** for anomaly detection, and **MongoDB** for persistence.

---

## 🚀 Features

* 📡 **Live Stock News Fetching** via **Perplexity API**
* 🧠 **Real-time Vector Memory** using **Pathway** (RAG-style retrieval)
* 💾 **Persistent Storage** of raw news in **MongoDB**
* 🔍 **Anomaly Detection** powered by **Claude 3.5 Sonnet**
* ⚖️ **Threat Level Scoring (0–10)** with reasoning based on past cases
* 💬 **Follow-up Questions** (Chat-style queries for deeper insights)
* ⚡ FastAPI + Uvicorn backend with **REST API** endpoints

---

## 🏗️ System Architecture

```
        ┌──────────────┐
        │   User Query │
        └──────┬───────┘
               │
         /analyze (FastAPI)
               │
   ┌───────────┴─────────────┐
   │                         │
Perplexity API         Pathway Memory (Vector DB)
 (latest news)         + MongoDB (persistent store)
   │                         │
   └───────────┬─────────────┘
               │
         Claude 3.5 Sonnet
     (Anomaly detection + summary)
               │
      Threat Score (0–10) + Report
```

---

## 🛠️ Tech Stack

* **Backend Framework**: FastAPI (Python)
* **Vector Database / Memory**: Pathway (real-time indexing + retrieval)
* **Embeddings Model**: BGE-base-en-v1.5 (Hugging Face)
* **LLM Reasoning**: Claude 3.5 Sonnet (Anthropic)
* **External Data Source**: Perplexity API
* **Database**: MongoDB (stores raw news docs)
* **Server**: Uvicorn (ASGI for FastAPI)
* **Config & Secrets**: dotenv (.env)
* **Frontend (planned)**: React.js + TailwindCSS

---

## 📂 Project Structure

```
insideX/
│── backend/
│   ├── main.py          # FastAPI app entry
│   ├── llm.py           # LLM orchestration (Perplexity + Claude + Threat model)
│   ├── vector_store.py  # Pathway memory & retrieval
│   ├── embeddings.py    # Embedding model (BGE)
│   ├── db.py            # MongoDB helper (save/retrieve news)
│   └── requirements.txt # Python dependencies
│
│── frontend/ (planned)  # React.js + Tailwind UI
│
│── .env.example         # Sample env file
│── README.md            # Documentation
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/insideX.git
cd insideX
```

### 2️⃣ Setup Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/Mac
# OR
.venv\Scripts\activate      # Windows PowerShell
```

### 3️⃣ Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```ini
# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=insideX
MONGO_COLLECTION=news

# API Keys
perplexity_api=your_perplexity_api_key
perplexity_url=https://api.perplexity.ai/chat/completions
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 5️⃣ Start Server

```bash
uvicorn backend.main:app --reload
```

---

## 🔎 Usage

### API Endpoint: Analyze Stock

**POST** `/analyze`
Request body:

```json
{
  "stock": "Tata Motors"
}
```

Response:

```json
{
  "stock": "Tata Motors",
  "perplexity_analysis": "...",
  "retrieved_context": [...],
  "final_report": [
    "• Anomaly detected in EV unit... (source link)",
    "• No issue found in quarterly earnings... (source link)",
    "• Threat Score: 7/10"
  ]
}
```

---

## 📊 Example Workflow

1. User queries: `"Analyze Tata Motors"`
2. **Perplexity** fetches latest stock news.
3. News gets stored in **MongoDB** + **Pathway memory** (for RAG).
4. **Claude AI** summarizes anomalies into **5 bullet points**.
5. A **Threat Score (0–10)** is generated based on past similar cases.
6. User can ask **follow-up questions** (“What was all-time high?”).

---

## 🌱 Future Work

* 📈 Add frontend dashboard (React + Tailwind)
* 🔔 Real-time alerts (email/Slack integration)
* ⚡ Upgrade Pathway to ANN index (HNSW/USearch) for scaling
* 📊 Add stock price + chart integration
* 🔮 More advanced risk modeling

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Open a PR or start a discussion under Issues.

---

## 📜 License

MIT License © 2025 insideX

