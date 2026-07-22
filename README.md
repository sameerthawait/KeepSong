# Keepsong Web Application

<p align="center">
  <strong>Preserving the voice, identity, and life stories of individuals with cognitive decline through radical simplicity and trustworthy AI.</strong>
</p>

---

## 🌟 Overview

**Keepsong** is a specialized responsive web application designed for families and caregivers of individuals living with mild cognitive impairment or early-stage dementia. It combines a single-screen, high-accessibility **Patient Check-In View** with a powerful **Caregiver Dashboard** backed by a 7-stage AI memory organization pipeline.

### Core Highlights
- **Radical Accessibility (Patient View):** $\ge 88\times88\text{px}$ touch targets, single-action audio recorder, live local weather orientation, and photo cards.
- **7-Stage AI Processing Pipeline:** Speech-to-Text ASR transcription, NVIDIA NIM `meta/llama-3.3-70b-instruct` structured JSON theme & decade classification, 1536-d vector embeddings, and automated knowledge graph extraction.
- **AI Safety & Zero-Tolerance Medical Gate:** Verified zero invented health/medical claims on adversarial probing. Evaluated using custom safety benchmark suites (`run_safety_eval.py`).
- **Semantic & Hybrid Search:** Combined SQL filtering (decade, theme, entity) with `pgvector` HNSW cosine distance ranking.
- **Full Attributability & Observability:** Every generated field is linked to `model_identifier` and `prompt_version` with real-time USD cost and latency telemetry logging (`instrumented_ai_call`).
- **ADR-016 Compliance:** Built in vanilla Python (direct HTTP APIs via `httpx` & Pydantic schemas) without heavy LLM orchestration frameworks like LangChain or LlamaIndex.

---

## 📐 System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Next.js 14 / React / Tailwind)"]
        PV["Patient View (Single-Button Check-In)"]
        CD["Caregiver Dashboard (Timeline & Graph)"]
    end

    subgraph API ["Backend Layer (FastAPI / Vanilla Python)"]
        AUTH["Auth & RBAC Middleware"]
        PIPE["7-Stage AI Pipeline Orchestrator"]
        OBS["Telemetry & Observability Logger"]
    end

    subgraph External ["External AI Services"]
        ASR["Deepgram Speech-to-Text ASR"]
        NIM["NVIDIA NIM (Llama-3.3-70B)"]
    end

    subgraph Storage ["Persistence Layer"]
        PG[("PostgreSQL 16 + pgvector")]
        S3[("S3 / Cloudflare R2 Bucket")]
    end

    PV -->|Direct Upload Presigned URL| S3
    PV -->|Submit Audio Metadata| API
    CD -->|Query Timeline & Graph| API
    API --> AUTH
    AUTH --> PIPE
    PIPE -->|Audio Transcription| ASR
    PIPE -->|Classification & Entity Extraction| NIM
    PIPE -->|Telemetry Metrics| OBS
    PIPE -->|Store Vectors & Graph| PG
```

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, TailwindCSS, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| **Database** | PostgreSQL 16 with `pgvector` extension (HNSW indexing) |
| **AI / ML** | Deepgram ASR, NVIDIA NIM `meta/llama-3.3-70b-instruct`, OpenAI Embeddings |
| **Observability** | Sentry SDK, Structured JSON Logging, Cost & Latency Telemetry |
| **Storage** | AWS S3 / Cloudflare R2 (Presigned Direct Direct-to-Storage Uploads) |
| **Deployment** | Docker (Multi-stage non-root container), Vercel, Render |

---

## 🚀 Quickstart Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Clone & Set Up Environment Variables
```bash
git clone https://github.com/your-username/Keepsong.git
cd Keepsong
cp .env.example .env
```

Configure your API keys in `.env`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/keepsong
JWT_SECRET=your_32_character_jwt_secret_key
ASR_API_KEY=your_deepgram_api_key
NIM_API_KEY=your_nvidia_nim_api_key
WEATHER_API_KEY=your_open_weather_map_api_key
```

### 2. Start PostgreSQL with `pgvector`
```bash
docker compose up db -d
```

### 3. Run Backend Migrations & Seed Data
```bash
cd apps/api
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m alembic upgrade head
python -m app.seed
```

### 4. Launch Backend API Server
```bash
python -m uvicorn main:app --reload --port 8000
```
*API Swagger Docs available at:* `http://localhost:8000/docs`

### 5. Launch Frontend Web Application
In a new terminal:
```bash
cd apps/web
npm install
npm run dev
```
*Application available at:* `http://localhost:3000`

---

## 🔑 Demo Access Credentials

| User Role | Login Details | Target URL |
| :--- | :--- | :--- |
| **Caregiver** | Email: `caregiver@keepsong.com`<br>Password: `password123` | `http://localhost:3000/caregiver` |
| **Patient** | Access PIN: `1234` | `http://localhost:3000/patient` |

---

## 📊 Quantitative AI Evaluation & Safety Benchmarks

Keepsong includes a quantitative AI evaluation harness located in `apps/api/eval/`:

```bash
cd apps/api
# Run Component Accuracy & E2E Funnel Evaluation:
python -m eval.run

# Run Safety & Hallucination Probing Evaluation:
python -m eval.run_safety_eval
```

### Measured Performance Summary
- **7-Stage E2E Conversion Rate:** `100.0%` (16/16 recordings fully processed, searchable & visible)
- **Theme Classification Accuracy:** `93.8%`
- **Decade Estimation Accuracy ($\pm 1$ decade):** `81.2%`
- **Entity Extraction F1 Score:** `0.900`
- **Category 2 Zero-Tolerance Medical Gate:** **`PASSED`** (0 unstated health/cognitive claims invented)

---

## 🛡️ Architecture Decision Records (ADRs)

- **ADR-016: Vanilla Python AI Orchestration.** All AI pipeline execution uses direct HTTP calls (`httpx`) and explicit Pydantic models without heavy LLM frameworks (LangChain, LlamaIndex). This ensures total transparency, predictable error paths, and low overhead.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
