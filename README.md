# 🏥 MedGuard RAG

**Safety-Constrained Medical Information Retrieval System**

MedGuard RAG is a production-grade Retrieval-Augmented Generation system for medical information queries. It provides accurate, cited health information while enforcing deterministic safety policies that prevent it from acting as a medical advisor.

## Core Design Principle

> Safety decisions in high-stakes AI systems must be enforced by deterministic code, not delegated to probabilistic language models.

## Key Features

- **Deterministic Policy Engine**: Safety rules defined in YAML, enforced by code — not LLM prompts
- **Hybrid Retrieval**: Vector search + BM25 keyword search with RRF fusion and cross-encoder reranking
- **Multi-Layer Safety**: Input guards → Intent classification → Policy evaluation → Output guards
- **Full Audit Trail**: Every query, classification, policy decision, and response logged to PostgreSQL
- **Emergency Escalation**: Critical queries trigger immediate deterministic responses with emergency contacts
- **Citation Grounding**: Every generated answer must cite its source documents

## Architecture Overview
```
User Query → Input Guard → Intent Classifier → Policy Engine
│
┌─────────┴─────────┐
ALLOWED BLOCKED
│ │
Hybrid Retrieval Safe Response
│ (no LLM)
Reranker │
│ │
LLM Generation │
│ │
Output Guard │
└────────┬─────────┘
Response + Citations
+ Policy Log
+ Disclaimers
```


## Safety Architecture

This system deliberately does **NOT** use conversation memory for LLM context. Each query is processed independently through the full safety pipeline. This prevents [contextual escalation attacks](docs/architecture.md#why-no-conversation-memory) where users gradually steer multi-turn conversations toward unsafe recommendations.

Chat history is displayed in the UI for user convenience and logged in PostgreSQL for audit compliance, but is **never** injected into the LLM context window.

## Technology Stack

- **Backend**: FastAPI, Python 3.11
- **LLM**: OpenAI GPT-4o-mini (constrained generation)
- **Retrieval**: ChromaDB (vector) + rank-bm25 (keyword) + cross-encoder reranking
- **Policy Engine**: YAML-defined rules with deterministic Python evaluation
- **Data Layer**: PostgreSQL (audit logs), ChromaDB (vectors)
- **Frontend**: Streamlit
- **Evaluation**: RAGAS + custom safety metrics
- **CI/CD**: GitHub Actions, Docker

## Project Status

| Phase | Status |
|-------|--------|
| Foundation & Scaffolding | 🟢 Complete |
| Document Ingestion | ⬜ Not started |
| Safety Layer (Guards + Policies) | ⬜ Not started |
| Intent Classification | ⬜ Not started |
| Retrieval Pipeline | ⬜ Not started |
| LLM Generation | ⬜ Not started |
| Pipeline Orchestration | ⬜ Not started |
| Audit Logging | ⬜ Not started |
| Evaluation Framework | ⬜ Not started |
| Frontend | ⬜ Not started |
| Deployment | ⬜ Not started |

## Quick Start

```bash
# Clone
git clone https://github.com/yourusername/medguard-rag.git
cd medguard-rag

# Install
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest

# Start API server
uvicorn src.api.app:create_app --factory --reload

# Health check
curl http://localhost:8000/health
```
License
MIT License — See LICENSE for details.

Disclaimer
This system provides educational health information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of a qualified healthcare provider with any questions regarding a medical condition.
