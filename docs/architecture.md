# MedGuard RAG — Architecture Document

## Design Principles

### 1. Safety by Deterministic Code
Safety decisions are made by the Policy Engine — a deterministic, rule-based
system that evaluates YAML-defined policies against classified intent and risk.
The LLM is never trusted to make safety decisions.

### 2. Single-Turn Processing
Each query is processed independently through the full pipeline. There is no
conversation memory injected into the LLM context.

### Why No Conversation Memory

Multi-turn memory in medical AI creates a **contextual escalation risk**:

1. User asks a safe general question (Turn 1: "What is ibuprofen?")
2. User asks about dosages educationally (Turn 2: "What are common adult doses?")
3. User asks for personal advice, leveraging context (Turn 3: "So should I take 400mg for my headache?")

With conversation memory, the LLM has normalized the topic across turns and is
significantly more likely to provide a personalized recommendation — violating
safety policy MED-004.

Without memory, Turn 3 is evaluated cold by the intent classifier and correctly
flagged as a dosage_request with HIGH risk, triggering policy MED-004 (DENY).

### 3. Full Audit Trail
Every query, classification, policy decision, and response is logged to
PostgreSQL. This is for compliance and debugging — never for LLM context.

## Pipeline Flow

Query → Input Guard → Intent Classifier → Policy Engine → [Retrieval | Safe Response] → Output Guard → Response


Each stage produces a typed Pydantic model that feeds into the next stage, creating a fully traceable pipeline.

